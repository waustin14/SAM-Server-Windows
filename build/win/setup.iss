[Setup]
AppName=SAM Service
AppVersion=0.1.0
DefaultDirName={pf}\SAMService
DefaultGroupName=SAM Service
OutputBaseFilename=SAM-Service-Setup
ArchitecturesInstallIn64BitMode=x64
; SignTool parameters omitted for brevity

[Files]
Source: "sam_server.py";         DestDir: "{app}"
Source: "sam_service.py";        DestDir: "{app}"
Source: "requirements.txt";      DestDir: "{app}"
Source: "scripts\download_model.py"; DestDir: "{app}\scripts"
Source: "scripts\postinstall.ps1";   Destdir: "{app}\scripts"
Source: "bin\python-3.11.9-embed-amd64.zip"; DestDir: "{app}\bin"

[Run]
Filename: "powershell.exe"; \
Parameters: "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File ""{app}\scripts\postinstall.ps1"""; \
Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;