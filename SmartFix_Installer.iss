; =============================================================================
; SmartFix AI — Inno Setup Installer Script
; Builds: SmartFix_Setup.exe
; Requirements: Inno Setup 6+ (https://jrsoftware.org/isdl.php)
; =============================================================================

#define MyAppName       "SmartFix AI"
#define MyAppVersion    "1.1.0"
#define MyAppPublisher  "Chirag Patil"
#define MyAppURL        "https://github.com/12Chirag12/Smart-Fix"
#define MyAppExeName    "SmartFix AI.exe"

[Setup]
AppId                     = {{A7E3F2C1-88D4-4B0A-9C1F-2E7D3B4A5F6E}
AppName                   = {#MyAppName}
AppVersion                = {#MyAppVersion}
AppPublisher              = {#MyAppPublisher}
AppPublisherURL           = {#MyAppURL}
AppSupportURL             = {#MyAppURL}
AppUpdatesURL             = {#MyAppURL}
DefaultDirName            = {autopf}\SmartFix AI
DefaultGroupName          = SmartFix AI
AllowNoIcons              = yes
LicenseFile               = {#SourcePath}\LICENSE
PrivilegesRequired        = admin
OutputDir                 = {#SourcePath}\dist\installer
OutputBaseFilename        = SmartFix_Setup
SetupIconFile             =
Compression               = lzma2/ultra64
SolidCompression          = yes
WizardStyle               = modern
WizardSmallImageFile      =
DisableWelcomePage        = no
DisableDirPage            = no
DisableReadyPage          = no
ShowLanguageDialog        = no
UninstallDisplayIcon      = {app}\{#MyAppExeName}
UninstallDisplayName      = {#MyAppName}
CloseApplications         = yes
RestartIfNeededByRun      = no
ChangesEnvironment        = yes
ArchitecturesInstallIn64BitMode = x64compatible
; Minimum Windows 10
MinVersion                = 10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut";      GroupDescription: "Additional shortcuts:"
Name: "startupicon"; Description: "Start SmartFix AI with &Windows"; GroupDescription: "Additional shortcuts:"

[Files]
; ── SmartFix application files ────────────────────────────────────────────────
Source: "{#SourcePath}\smartfix_app.py";          DestDir: "{app}";         Flags: ignoreversion
Source: "{#SourcePath}\SmartFix AI.exe";          DestDir: "{app}";         Flags: ignoreversion
Source: "{#SourcePath}\requirements.txt";         DestDir: "{app}";         Flags: ignoreversion
Source: "{#SourcePath}\install_helper.ps1";       DestDir: "{app}";         Flags: ignoreversion

; ── Monitor module (all Python files including new Lab Monitor modules) ────────
Source: "{#SourcePath}\monitor\*.py";             DestDir: "{app}\monitor"; Flags: ignoreversion
Source: "{#SourcePath}\monitor\__init__.py";      DestDir: "{app}\monitor"; Flags: ignoreversion

; ── Data directory (existing data, skip if source doesn't exist) ──────────────
Source: "{#SourcePath}\data\*";                   DestDir: "{app}\data";    Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Dirs]
Name: "{app}\data"
Name: "{app}\logs"
Name: "{app}\monitor"
Name: "{app}\monitor\__pycache__"

[Icons]
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; Comment: "SmartFix AI — Windows Error Monitor & Lab Monitor"
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";      Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Auto-start with Windows in background (also registered via schtasks in install_helper.ps1)
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SmartFix AI"; ValueData: """{app}\{#MyAppExeName}"" --background"; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; ── Main dependency installer (Python + packages + Ollama + llama3 + firewall) ──
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -WindowStyle Normal -File ""{app}\install_helper.ps1"" -InstallDir ""{app}"""; \
    StatusMsg: "Installing Python, PyQt6, Ollama, llama3 model and Lab Monitor firewall rules... (may take 10-30 min)"; \
    Flags: waituntilterminated; \
    Description: "Install all dependencies (Python, PyQt6, Ollama AI, llama3 model)"

; ── Launch after install ───────────────────────────────────────────────────────
Filename: "{app}\{#MyAppExeName}"; \
    Description: "Launch {#MyAppName} now"; \
    Flags: nowait postinstall skipifsilent shellexec

[UninstallRun]
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""schtasks /Delete /TN 'SmartFix AI Autostart' /F -ErrorAction SilentlyContinue; Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' -Name 'SmartFix AI' -ErrorAction SilentlyContinue; Remove-Item -Path '$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\SmartFix AI.lnk' -ErrorAction SilentlyContinue; Remove-NetFirewallRule -DisplayName 'SmartFix-Lab-*' -ErrorAction SilentlyContinue"""; \
    Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\monitor\__pycache__"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\install_log.txt"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
