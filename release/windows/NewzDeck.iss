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
  WM_CLOSE = $0010;
  PROCESS_TERMINATE = $0001;
  SYNCHRONIZE = $00100000;
  WAIT_OBJECT_0 = 0;
  WAIT_TIMEOUT = 258;

var
  ServiceWasInstalled: Boolean;
  TrayAutostartWasEnabled: Boolean;

function GetWindowThreadProcessId(hWnd: HWND; var ProcessId: DWORD): DWORD;
  external 'GetWindowThreadProcessId@user32.dll stdcall';
function OpenProcess(DesiredAccess: DWORD; InheritHandle: Integer; ProcessId: DWORD): THandle;
  external 'OpenProcess@kernel32.dll stdcall';
function WaitForSingleObject(Handle: THandle; Milliseconds: DWORD): DWORD;
  external 'WaitForSingleObject@kernel32.dll stdcall';
function TerminateProcess(Handle: THandle; ExitCode: DWORD): Integer;
  external 'TerminateProcess@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): Integer;
  external 'CloseHandle@kernel32.dll stdcall';

function ServiceInstalled(): Boolean;
begin
  Result := RegKeyExists(HKLM, ServiceRegKey);
end;

function RunElevatedAndWait(const FileName, Parameters, WorkingDir: String; var ResultCode: Integer): Boolean;
begin
  { Avoid an unnecessary runas/UAC hop when Setup already has administrative
    rights (for example on managed or CI systems). Normal per-user installs
    still request elevation only for the service maintenance helper. }
  if IsAdmin then
    Result := Exec(FileName, Parameters, WorkingDir, SW_HIDE, ewWaitUntilTerminated, ResultCode)
  else
    Result := ShellExec('runas', FileName, Parameters, WorkingDir, SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function QuoteArg(const S: String): String;
begin
  Result := '"' + S + '"';
end;

function CloseExistingTrayForUpgrade(): String;
var
  TrayWindow: HWND;
  TrayProcess: THandle;
  TrayPid: DWORD;
  WaitResult: DWORD;
  Attempt: Integer;
  Poll: Integer;
begin
  Result := '';

  { A hidden window can disappear before the owning Go process has finished
    unwinding and released NewzDeckTray.exe. Capture the process handle BEFORE
    WM_CLOSE, then wait on the process itself. }
  for Attempt := 1 to 4 do
  begin
    TrayWindow := FindWindowByClassName('NewzDeckTrayWindow');
    if TrayWindow = 0 then
    begin
      Sleep(250);
      TrayWindow := FindWindowByClassName('NewzDeckTrayWindow');
      if TrayWindow = 0 then
      begin
        Sleep(300);
        Exit;
      end;
    end;

    TrayPid := 0;
    GetWindowThreadProcessId(TrayWindow, TrayPid);
    TrayProcess := 0;
    if TrayPid <> 0 then
      TrayProcess := OpenProcess(SYNCHRONIZE or PROCESS_TERMINATE, 0, TrayPid);

    PostMessage(TrayWindow, WM_CLOSE, 0, 0);

    if TrayProcess <> 0 then
    begin
      WaitResult := WaitForSingleObject(TrayProcess, 10000);
      if WaitResult = WAIT_TIMEOUT then
      begin
        Log('NewzDeck tray did not exit after WM_CLOSE; using bounded forced termination.');
        if TerminateProcess(TrayProcess, 0) = 0 then
        begin
          CloseHandle(TrayProcess);
          Result := 'NewzDeck Setup could not close the existing tray companion. Setup stopped before replacing application files. Exit NewzDeck from the notification area or restart Windows, then run Setup again.';
          Exit;
        end;
        WaitResult := WaitForSingleObject(TrayProcess, 5000);
      end;

      CloseHandle(TrayProcess);
      if WaitResult <> WAIT_OBJECT_0 then
      begin
        Result := 'NewzDeck Setup could not confirm that the existing tray companion exited. Setup stopped before replacing application files. Exit NewzDeck from the notification area or restart Windows, then run Setup again.';
        Exit;
      end;
    end
    else
    begin
      for Poll := 1 to 50 do
      begin
        if FindWindowByClassName('NewzDeckTrayWindow') = 0 then
        begin
          Sleep(750);
          Break;
        end;
        Sleep(100);
      end;

      if FindWindowByClassName('NewzDeckTrayWindow') <> 0 then
      begin
        Result := 'NewzDeck Setup could not close the existing tray companion. Setup stopped before replacing application files. Exit NewzDeck from the notification area or restart Windows, then run Setup again.';
        Exit;
      end;
    end;
  end;

  Sleep(300);
end;

procedure InitializeWizard();
begin
  { Keep the installer visible above ordinary application windows. }
  WizardForm.FormStyle := fsStayOnTop;
end;

function StopExistingServiceForUpgrade(): String;
var
  Helper: String;
  ResultCode: Integer;
begin
  Result := '';
  if not ServiceWasInstalled then
    Exit;

  Helper := ExpandConstant('{app}\NewzDeckService.exe');
  if not FileExists(Helper) then
  begin
    Result := 'The existing NewzDeck background service is installed, but its service helper is missing. Setup stopped before replacing any application files. Repair or remove the background service, then run Setup again.';
    Exit;
  end;

  { Use the installed helper rather than guessing how long Windows needs after
    SC STOP. NewzDeckService.exe stop waits for the SCM state to reach STOPPED
    (bounded by 25 seconds) and also allows the managed backend time to exit. }
  if not RunElevatedAndWait(Helper, 'stop', ExpandConstant('{app}'), ResultCode) then
  begin
    Result := 'Windows did not allow NewzDeck Setup to stop the existing background service. Setup stopped before replacing any application files. Approve the elevation prompt and try again.';
    Exit;
  end;

  if ResultCode <> 0 then
  begin
    Result := 'The existing NewzDeck background service did not stop cleanly (error ' + IntToStr(ResultCode) + '). Setup stopped before replacing any application files. Try again after closing NewzDeck, or restart Windows if the service remains stuck.';
    Exit;
  end;

  { The helper process itself has now exited, so its executable handle is gone.
    Give filesystem filter drivers a brief scheduling turn before file overlay. }
  Sleep(300);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  ServiceWasInstalled := ServiceInstalled();
  TrayAutostartWasEnabled := RegValueExists(HKCU, TrayRunKey, TrayRunValue);

  { Close the signed-in-user tray companion and wait for the real process to
    exit before Inno's Restart Manager/file overlay work begins. }
  Result := CloseExistingTrayForUpgrade();
  if Result <> '' then
    Exit;

  if ServiceWasInstalled then
  begin
    Result := StopExistingServiceForUpgrade();
    if Result <> '' then
      Exit;
  end;
end;

procedure RepairExistingService();
var
  Helper, Params, UserRoot, DefaultDownload, UserProfile: String;
  ResultCode: Integer;
begin
  if not ServiceWasInstalled then
    Exit;

  Helper := ExpandConstant('{app}\NewzDeckService.exe');
  UserRoot := ExpandConstant('{localappdata}\NewzDeck');

  { Inno Setup has no user-profile shell-folder constant. Resolve the Windows
    USERPROFILE environment variable at install time, with a safe fallback. }
  UserProfile := GetEnv('USERPROFILE');
  if UserProfile = '' then
    UserProfile := ExpandConstant('{localappdata}');
  DefaultDownload := PathCombine(UserProfile, 'Downloads\NewzDeck');

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
