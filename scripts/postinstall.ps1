$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ---------- 1) Ensure Python ----------
$pyExe = (Get-Command python.exe -ErrorAction SilentlyContinue)?.Source
if (-not $pyExe) {
  Expand-Archive "$dir\bin\python-3.11.9-embed-amd64.zip" "$dir\Python"
  $pyExe = "$dir\Python\python.exe"
}

# ---------- 2) venv ----------
& $pyExe -m venv "$dir\venv"
& "$dir\venv\Scripts\python.exe" -m pip install --upgrade pip

# ---------- 3) deps ----------
& "$dir\venv\Scripts\pip.exe" install -r "$dir\requirements.txt"
# GPU users can add:
& "$dir\venv\Scripts\pip.exe" install torch torchvision --index-url https://download.pytorch.org/whl/cu121
& "$dir\venv\Scripts\python.exe" -m pywin32_postinstall -install

# ---------- 4) create service ----------
& "$dir\venv\Scripts\python.exe" "$dir\sam_service.py" remove 2>$null   # ignore if not installed
& "$dir\venv\Scripts\python.exe" "$dir\sam_service.py" install          # adds to SCM
& sc.exe config $svcName start= auto         # auto‑start at boot

# ---------- 5) model ----------
& "$dir\venv\Scripts\python.exe" "$dir\scripts\download_model.py" "$dir\models\sam_vit_h.pth"

# ---------- 6) start service ----------
$svcName = "SAMService"
& sc.exe start $svcName