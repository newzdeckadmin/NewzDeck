#ifndef AppVersion
  #error AppVersion must be supplied by build-release.ps1
#endif
#ifndef PayloadDir
  #error PayloadDir must be supplied by build-release.ps1
#endif
#ifndef OutputDir
  #error OutputDir must be supplied by build-release.ps1
#endif

#define AppName "NewzDeck"
#define AppExeName "NewzDeck.exe"
#define IntegrationExeName "NewzDeck.Integration.exe"

[Setup]
; Keep this AppId stable. It identifies all NewzDeck upgrades as one product and
; lets Inno Setup preserve the existing uninstall journal across upgrades.
AppId=NewzDeck
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=NewzDeck
DefaultDirName={localappdata}\Programs\NewzDeck
DefaultGroupName=NewzDeck
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=NewzDeck_v{#AppVersion}_Setup
SetupIconFile={#PayloadDir}\NewzDeck.ico
UninstallDisplayIcon={app}\{#AppExeName}
VersionInfoVersion={#AppVersion}.0
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
DirExistsWarning=no
SetupLogging=yes
Uninstallable=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; VERSION.txt is intentionally installed and also included in the portable ZIP,
; so both public packages can be traced to the exact same tested payload.
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs restartreplace

[Icons]
Name: "{autoprograms}\NewzDeck"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\NewzDeck"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; If the tested payload contains the existing application-owned integration
; helper, use it to repair/migrate background-service and tray registration.
; Existing registrations otherwise remain untouched during an in-place upgrade.
Filename: "{app}\{#IntegrationExeName}"; Parameters: "repair --install-root ""{app}"" --data-root ""{localappdata}\NewzDeck"""; StatusMsg: "Repairing NewzDeck background integration..."; Flags: runhidden waituntilterminated skipifdoesntexist
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,NewzDeck}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; The helper removes the service/tray integration only. Persistent data under
; %LOCALAPPDATA%\NewzDeck is deliberately retained.
Filename: "{app}\{#IntegrationExeName}"; Parameters: "remove --install-root ""{app}"" --data-root ""{localappdata}\NewzDeck"" --preserve-user-data"; Flags: runhidden waituntilterminated skipifdoesntexist; RunOnceId: "RemoveNewzDeckIntegration"

; There is intentionally no [InstallDelete] or [UninstallDelete] section. Inno
; Setup removes files it installed under {app}; it never removes the persistent
; {localappdata}\NewzDeck data tree during an upgrade or uninstall.
