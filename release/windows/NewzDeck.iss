#ifndef AppVersion
  #error AppVersion must be supplied by build-release.ps1
#endif
#ifndef PayloadDir
  #error PayloadDir must be supplied by build-release.ps1
#endif
#ifndef OutputDir
  #error OutputDir must be supplied by build-release.ps1
#endif

#define MyAppName "NewzDeck"
#define MyAppExeName "NewzDeck.exe"
#define MyPublisher "NewzDeck"
#define MyURL "https://www.newzdeck.com"

[Setup]
; Stable product identity from the proven v3.5.31+ installer. Never change this.
AppId={{A84C814C-704C-4C7D-A20B-BA5DD83F9429}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} v{#AppVersion}
AppPublisher={#MyPublisher}
AppPublisherURL={#MyURL}
AppSupportURL={#MyURL}
AppUpdatesURL={#MyURL}
DefaultDirName={localappdata}\Programs\NewzDeck
DefaultGroupName=NewzDeck
DisableProgramGroupPage=yes
AllowNoIcons=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupArchitecture=x64
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=NewzDeck_v{#AppVersion}_Setup
SetupIconFile={#PayloadDir}\NewzDeck.ico
UninstallDisplayName=NewzDeck
UninstallDisplayIcon={app}\NewzDeck.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
CloseApplicationsFilter=NewzDeck.exe,NewzDeckService.exe,NewzDeckTray.exe,NewzDeckPicker.exe,NewzDeckThumb.exe,NewzDeckYenc.exe
UsePreviousAppDir=yes
UsePreviousTasks=yes
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany=NewzDeck
VersionInfoDescription=NewzDeck Setup
VersionInfoProductName=NewzDeck
VersionInfoProductVersion={#AppVersion}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Overlay the exact source-built payload. Extra/generated files in the install
; directory are deliberately not purged during upgrades.
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\NewzDeck"; Filename: "{app}\NewzDeck.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NewzDeck.ico"
Name: "{autodesktop}\NewzDeck"; Filename: "{app}\NewzDeck.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NewzDeck.ico"; Tasks: desktopicon

; NewzDeck is intentionally not auto-launched from inside Setup. Users launch
; NewzDeck normally after Setup exits, avoiding upgrade/startup handoff races.

[Code]
const
  ServiceRegKey = 'SYSTEM\CurrentControlSet\Services\NewzDeckService';
  TrayRunKey = 'Software\Microsoft\Windows\CurrentVersion\Run';
  TrayRunValue = 'NewzDeckTray';

var
  ServiceWasInstalled: Boolean;
  TrayAutostartWasEnabled: Boolean;

function ServiceInstalled(): Boolean;
begin
  Result := RegKeyExists(HKLM, ServiceRegKey);
end;

function RunElevatedAndWait(const FileName, Parameters, WorkingDir: String; var ResultCode: Integer): Boolean;
begin
  Result := ShellExec('runas', FileName, Parameters, WorkingDir, SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function QuoteArg(const S: String): String;
begin
  Result := '"' + S + '"';
end;

procedure InitializeWizard();
begin
  { Keep the installer visible above ordinary application windows. }
  WizardForm.FormStyle := fsStayOnTop;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  ServiceWasInstalled := ServiceInstalled();
  TrayAutostartWasEnabled := RegValueExists(HKCU, TrayRunKey, TrayRunValue);

  if ServiceWasInstalled then
  begin
    { Stop the old service before its executable is overlaid. SC returns a
      non-zero code if the service is already stopped, so failure is tolerated
      here; Inno's subsequent file-lock handling remains authoritative. }
    RunElevatedAndWait(ExpandConstant('{sys}\sc.exe'), 'stop NewzDeckService', '', ResultCode);
    Sleep(1200);
  end;
end;

procedure RepairExistingService();
var
  Helper, Params, UserRoot, DefaultDownload: String;
  ResultCode: Integer;
begin
  if not ServiceWasInstalled then
    Exit;

  Helper := ExpandConstant('{app}\NewzDeckService.exe');
  UserRoot := ExpandConstant('{localappdata}\NewzDeck');
  DefaultDownload := ExpandConstant('{userprofile}\Downloads\NewzDeck');
  Params := 'repair --user-root ' + QuoteArg(UserRoot) +
            ' --default-download-dir ' + QuoteArg(DefaultDownload);

  if not RunElevatedAndWait(Helper, Params, ExpandConstant('{app}'), ResultCode) then
    MsgBox('NewzDeck was installed, but Windows did not allow the existing background service to be repaired. Open NewzDeck > Settings > Background Service and choose Repair.', mbError, MB_OK)
  else if ResultCode <> 0 then
    MsgBox('NewzDeck was installed, but background-service repair returned error code ' + IntToStr(ResultCode) + '. Open NewzDeck > Settings > Background Service and choose Repair.', mbError, MB_OK);
end;

procedure RefreshTrayAutostart();
var
  Cmd: String;
begin
  if not TrayAutostartWasEnabled then
    Exit;

  Cmd := QuoteArg(ExpandConstant('{app}\NewzDeckTray.exe')) +
         ' --app-dir ' + QuoteArg(ExpandConstant('{app}')) +
         ' --user-root ' + QuoteArg(ExpandConstant('{localappdata}\NewzDeck')) +
         ' --version {#AppVersion}';
  RegWriteStringValue(HKCU, TrayRunKey, TrayRunValue, Cmd);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    RepairExistingService();
    RefreshTrayAutostart();
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  { Reassert foreground/topmost state after page changes so folder/UAC handoffs
    cannot leave the main installer hidden behind other windows. }
  WizardForm.FormStyle := fsStayOnTop;
  WizardForm.BringToFront;
end;

function InitializeUninstall(): Boolean;
var
  Helper: String;
  ResultCode: Integer;
begin
  Result := True;
  if ServiceInstalled() then
  begin
    Helper := ExpandConstant('{app}\NewzDeckService.exe');
    if FileExists(Helper) then
    begin
      if not RunElevatedAndWait(Helper, 'uninstall', ExpandConstant('{app}'), ResultCode) then
      begin
        MsgBox('Windows did not allow the NewzDeck background service to be removed. Uninstall was cancelled so the service is not orphaned.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
      if ResultCode <> 0 then
      begin
        MsgBox('The NewzDeck background service could not be removed (error ' + IntToStr(ResultCode) + '). Uninstall was cancelled so the service is not orphaned.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
    end;
  end;

  { The tray autostart command points into the application directory and must not
    survive uninstall. Persistent user data remains untouched. }
  RegDeleteValue(HKCU, TrayRunKey, TrayRunValue);
end;
