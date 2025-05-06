$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$svcName = "SAMService"

# ---------- 1) Ensure Python ----------
$pyCmd = Get-Command python.exe -ErrorAction SilentlyContinue
$pyExe = if ($pyCmd) { $pyCmd.Source } else { $null }
if (-not $pyExe) {
  Expand-Archive "$dir\..\bin\python-3.11.9-embed-amd64.zip" "$dir\Python"
  $pyExe = "$dir\Python\python.exe"
}

# ---------- 2) venv ----------
& $pyExe -m venv "$dir\venv"
# Activate the virtual environment
& "$dir\venv\Scripts\Activate.ps1"
# Upgrade pip
& "$dir\venv\Scripts\pip.exe" --upgrade pip

# ---------- 3) deps ----------
& "$dir\venv\Scripts\pip.exe" install -r "$dir\..\requirements.txt"

# Check for NVIDIA GPU
$hasNvidiaGPU = $false
try {
    $gpu = Get-WmiObject Win32_VideoController | Where-Object { $_.Name -match "NVIDIA" }
    $hasNvidiaGPU = $null -ne $gpu
} catch {
    Write-Warning "Failed to check for NVIDIA GPU: $_"
}

# Install PyTorch with CUDA support only if NVIDIA GPU is present
if ($hasNvidiaGPU) {
    Write-Host "NVIDIA GPU detected. Installing PyTorch with CUDA support..."
    & "$dir\venv\Scripts\pip.exe" install torch==2.3.1+cu121 torchvision==0.18.1+cu121 --index-url https://download.pytorch.org/whl/cu121
} else {
    Write-Host "No NVIDIA GPU detected. Installing CPU-only PyTorch..."
    & "$dir\venv\Scripts\pip.exe" install torch torchvision
}

& "$dir\venv\Scripts\pywin32_postinstall.exe" -install

# ---------- 4) create service ----------
& "$dir\venv\Scripts\python.exe" "$dir\sam_service.py" remove 2>$null   # ignore if not installed
& "$dir\venv\Scripts\python.exe" "$dir\sam_service.py" install          # adds to SCM
& sc.exe config $svcName start= auto         # auto‑start at boot

# ---------- 5) model ----------
& "$dir\venv\Scripts\python.exe" "$dir\scripts\download_model.py" "C:\ProgramData\SAMService\sam_vit_h.pth"

# ---------- 6) start service ----------
& sc.exe start $svcName