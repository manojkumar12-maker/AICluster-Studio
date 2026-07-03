; =============================================================================
;  AICluster Setup - master Inno Setup installer
;  -----------------------------------------------------------------------------
;  This script is the source of truth for AIClusterSetup.exe. It is a
;  single-file wizard that:
;
;    * Detects (and installs) the Python 3.12+ runtime if missing
;    * Detects (and installs) the Microsoft Visual C++ 2015-2022 runtime
;    * Copies the prebuilt AICluster binaries to {app}
;    * Creates Start Menu + Desktop shortcuts
;    * Configures the Windows Firewall (inbound rules for the cluster ports)
;    * Creates the AICluster data folder and copies default configuration
;    * Runs a verification pass and offers to launch the Master service
;
;  The build system (build/setup/build_setup.py) injects the per-app
;  ProductVersion, AppId, app list, and bundling flags via #define values
;  that are passed on the ISCC command line:
;
;      ISCC setup.iss /DAppVersion=1.2.1 /DAppId=com.aicluster.setup ...
;
;  When compiled by build_setup.py all of these defines are supplied.
; =============================================================================

#define MyAppName "AICluster"
#define MyAppShortName "AICluster"
#define MyAppPublisher "AICluster"
#define MyAppCopyright "Copyright (c) 2026 AICluster"
#define MyAppURL "https://aicluster.local"
#define MyAppId "com.aicluster.setup"
#define MyAppExeName "AIClusterMaster.exe"
#define MyStudioExeName "AIClusterStudio.exe"
#define MyAppDataDir "AICluster"

#ifndef AppVersion
  #define AppVersion "1.2.1"
#endif
#ifndef AppId
  #define AppId MyAppId
#endif
#ifndef BundlePython
  #define BundlePython "1"
#endif
#ifndef BundleVCRedist
  #define BundleVCRedist "1"
#endif
#ifndef ConfigureFirewall
  #define ConfigureFirewall "1"
#endif
#ifndef LaunchMaster
  #define LaunchMaster "1"
#endif
#ifndef AppSourceDir
  #define AppSourceDir "payload\\aicluster"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} {#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright={#MyAppCopyright}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableReadyPage=no
DisableFinishedPage=no
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=AIClusterSetup-{#AppVersion}
SetupIconFile=assets\setup.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} {#AppVersion} Setup
UninstallDisplayName={#MyAppName} {#AppVersion}
UninstallFilesDir={app}\uninst
AppMutex=AIClusterSetupMutex,Global\AIClusterSetupMutex
SignedUninstaller=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
WelcomeLabel=Welcome to the AICluster Setup Wizard%n%nThis wizard will install the following components on your computer:%n%n  - AICluster Master Server%n  - AICluster Worker Service%n  - AICluster Studio (Visual IDE)%n  - Python 3.12+ Runtime (if not already installed)%n  - Microsoft Visual C++ 2015-2022 Redistributable%n%nThe setup will also configure the Windows Firewall and create the Start Menu / Desktop shortcuts for you.
PreflightTitle=Runtime Preflight Check
PreflightLabel=AICluster requires two runtime components to function correctly:%n%n  1. Microsoft Visual C++ 2015-2022 Redistributable (x64)%n  2. Python 3.12 or newer (64-bit)%n%nThe wizard will scan your system and install anything that is missing.
FirewallTitle=Windows Firewall
FirewallLabel=AICluster opens TCP ports on this machine to communicate with workers and clients:%n%n  - Port 8000  (AICluster Master API / WebSocket)%n  - Port 8001  (AICluster Worker service)%n  - Port 5174  (AICluster Master Control Center)%n  - Port 5175  (AICluster Worker Control Center)%n  - Port 1420  (Tauri IPC)%n%nThe wizard will register these as Windows Firewall inbound rules. You can change them later in "Control Panel -> System and Security -> Windows Defender Firewall".
VerifyTitle=Installation Verification
VerifyLabel=Verifying the installation...%n%nThis may take a few seconds. Once verification succeeds the Master Server will be ready to launch.
FinishedRunLabel=Launch AICluster Master when finished
FinishedShortcutLabel=Create a desktop shortcut
CreateDesktopIcon=Create a &desktop shortcut

[Types]
Name: "full"; Description: "Full installation (Master + Worker + Studio + all tools)"
Name: "compact"; Description: "Compact installation (Master only)"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "master"; Description: "AICluster Master Server (FastAPI + Web dashboard)"; Types: full compact custom; Flags: fixed
Name: "worker"; Description: "AICluster Worker Service"; Types: full custom
Name: "studio"; Description: "AICluster Studio (Visual IDE & Workspace)"; Types: full custom
Name: "python"; Description: "Embedded Python 3.12 runtime (used by all services)"; Types: full compact custom; Flags: fixed
Name: "vcredist"; Description: "Microsoft Visual C++ 2015-2022 Redistributable (x64)"; Types: full compact custom
Name: "firewall"; Description: "Configure Windows Firewall rules"; Types: full custom
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; Types: full compact custom

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; --- Master, Worker, Studio binaries (bundled prebuilt) ----------------
Source: "{#AppSourceDir}\master\*"; DestDir: "{app}\master"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: master
Source: "{#AppSourceDir}\worker\*"; DestDir: "{app}\worker"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: worker
Source: "{#AppSourceDir}\master-control\*"; DestDir: "{app}\master-control"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: master
Source: "{#AppSourceDir}\worker-control\*"; DestDir: "{app}\worker-control"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: worker
Source: "{#AppSourceDir}\studio\*"; DestDir: "{app}\studio"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: studio
Source: "{#AppSourceDir}\cli\*"; DestDir: "{app}\cli"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: master

; --- Bundled runtime installers (only if present) -----------------------
Source: "payload\python\python-3.12*-amd64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall; Check: ShouldInstallPython; Components: python
Source: "payload\vcredist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall; Check: ShouldInstallVCRedist; Components: vcredist

; --- Default configuration and assets ----------------------------------
Source: "payload\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: master
Source: "payload\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: master
Source: "payload\LAUNCH_INSTRUCTIONS.md"; DestDir: "{app}"; Flags: ignoreversion; Components: master

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\plugins"; Permissions: users-modify
Name: "{app}\models"; Permissions: users-modify
Name: "{commondocs}\{#MyAppDataDir}"; Permissions: users-modify
Name: "{commondocs}\{#MyAppDataDir}\data"; Permissions: users-modify
Name: "{commondocs}\{#MyAppDataDir}\logs"; Permissions: users-modify
Name: "{commondocs}\{#MyAppDataDir}\backups"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName} Master"; Filename: "{app}\master\{#MyAppExeName}"; WorkingDir: "{app}\master"; Comment: "Launch the AICluster Master server"; Components: master
Name: "{group}\{#MyAppName} Studio"; Filename: "{app}\studio\{#MyStudioExeName}"; WorkingDir: "{app}\studio"; Comment: "Launch AICluster Studio"; Components: studio
Name: "{group}\{#MyAppName} Worker"; Filename: "{app}\worker\AIClusterWorker.exe"; WorkingDir: "{app}\worker"; Comment: "Launch the AICluster Worker service"; Components: worker
Name: "{group}\{#MyAppName} CLI"; Filename: "{app}\cli\aicluster.exe"; WorkingDir: "{app}\cli"; Comment: "AICluster command-line interface"; Components: master
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"; Components: master
Name: "{commondesktop}\{#MyAppName} Master"; Filename: "{app}\master\{#MyAppExeName}"; WorkingDir: "{app}\master"; Comment: "Launch the AICluster Master server"; Tasks: desktopicon; Components: master
Name: "{commondesktop}\{#MyAppName} Studio"; Filename: "{app}\studio\{#MyStudioExeName}"; WorkingDir: "{app}\studio"; Comment: "Launch AICluster Studio"; Tasks: desktopicon; Components: studio

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Visual C++ 2015-2022 Redistributable..."; Check: ShouldInstallVCRedist; Flags: waituntilterminated; Components: vcredist
Filename: "{tmp}\python-3.12-amd64.exe"; Parameters: "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_doc=0 Include_launcher=0 Include_tcltk=0 TargetDir={app}\python"; StatusMsg: "Installing Python 3.12 runtime..."; Check: ShouldInstallPython; Flags: waituntilterminated; Components: python
#ifndef LaunchMaster
  #define LaunchMaster "1"
#endif
#if LaunchMaster == "1"
Filename: "{app}\master\AIClusterMaster.exe"; Description: "{cm:FinishedRunLabel}"; Flags: nowait runmaximized skipifsilent; Components: master
#endif

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C netsh advfirewall firewall delete rule name=""AICluster Setup - Inbound"" >nul 2>&1"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\plugins"
Type: filesandordirs; Name: "{app}\models"
Type: filesandordirs; Name: "{app}\uninst"
Type: filesandordirs; Name: "{commondocs}\{#MyAppDataDir}\data"
Type: filesandordirs; Name: "{commondocs}\{#MyAppDataDir}\logs"
Type: filesandordirs; Name: "{commondocs}\{#MyAppDataDir}\backups"

[Code]
// =============================================================================
//  PascalScript helpers
// =============================================================================
//  All logic that has to run on the user's machine is implemented here so the
//  installer remains a single, self-contained executable.
// =============================================================================

const
  APP_PYTHON_MIN_MAJOR = 3;
  APP_PYTHON_MIN_MINOR = 12;
  APP_VCREDIST_INSTALLER    = 'vc_redist.x64.exe';
  APP_FIREWALL_RULE_NAME    = 'AICluster Setup - Inbound';
  APP_DATA_DIR_NAME         = 'AICluster';

var
  APP_FIREWALL_PORTS: array of Integer;

var
  PreflightPage: TWizardPage;
  FirewallPage: TWizardPage;
  VerifyPage: TWizardPage;
  PreflightMemo: TMemo;
  PreflightStatus: TNewStaticText;
  PreflightRescanButton: TButton;
  FirewallCheck: TCheckBox;
  VerifyMemo: TMemo;
  VerifyStatus: TNewStaticText;
  PythonDetected: Boolean;
  VCRedistDetected: Boolean;
  ShouldConfigureFirewall: Boolean;
  ShouldLaunchMaster: Boolean;

procedure RunPowerShell(const Script: string; out Output: string);
var
  ResultCode: Integer;
begin
  Output := '';
  if not Exec('powershell.exe',
              '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' + Script + '"',
              '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    Output := 'PowerShell failed to launch';
  end
  else
    Output := 'PowerShell exit ' + IntToStr(ResultCode);
end;

function DetectVC2015Plus: Boolean;
var
  Script, OutStr: string;
begin
  Result := False;
  Script :=
    'if ((Test-Path ''HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64'') -or ' +
    '(Test-Path ''HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64'') -or ' +
    '(Test-Path ''HKLM:\SOFTWARE\Microsoft\VisualStudio\17.0\VC\Runtimes\x64'') -or ' +
    '(Test-Path ''HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\17.0\VC\Runtimes\x64'')) ' +
    '{ exit 0 } else { exit 1 }';
  RunPowerShell(Script, OutStr);
  Result := Pos('PowerShell exit 0', OutStr) > 0;
end;

function DetectPython(out ExePath: string): Boolean;
var
  Script, OutStr: string;
begin
  Result := False;
  ExePath := '';
  Script :=
    '$p = (Get-ItemProperty -Path ''HKLM:\SOFTWARE\Python\PythonCore\3.12\InstallPath'' -ErrorAction SilentlyContinue).ExecutablePath; ' +
    'if (-not $p) { $p = (Get-ItemProperty -Path ''HKLM:\SOFTWARE\Python\PythonCore\3.13\InstallPath'' -ErrorAction SilentlyContinue).ExecutablePath }; ' +
    'if (-not $p) { $p = (Get-ItemProperty -Path ''HKLM:\SOFTWARE\Python\PythonCore\3.14\InstallPath'' -ErrorAction SilentlyContinue).ExecutablePath }; ' +
    'if ($p -and (Test-Path $p)) { Write-Output $p; exit 0 } else { exit 1 }';
  RunPowerShell(Script, OutStr);
  if Pos('PowerShell exit 0', OutStr) > 0 then
  begin
    // Extract the pythonw.exe path from the output. The body is
    // everything before the "PowerShell exit" line.
    ExePath := Trim(OutStr);
    Delete(ExePath, Pos('PowerShell exit', ExePath),
           Length(ExePath));
    ExePath := Trim(ExePath);
    if FileExists(ExePath) then
      Result := True;
  end;
end;

procedure RefreshPreflight(Sender: TObject);
var
  PyVersion: string;
  Lines: TStringList;
begin
  PythonDetected := DetectPython(PyVersion);
  VCRedistDetected := DetectVC2015Plus;
  Lines := TStringList.Create;
  try
    Lines.Add('System preflight');
    Lines.Add('================');
    Lines.Add('');
    if PythonDetected then
      Lines.Add('[OK]   Python 3.12+ detected at: ' + PyVersion)
    else
      Lines.Add('[TODO] Python 3.12+ not detected - will be installed');
    if VCRedistDetected then
      Lines.Add('[OK]   Microsoft Visual C++ 2015-2022 Redistributable detected')
    else
      Lines.Add('[TODO] Microsoft Visual C++ Redistributable not detected - will be installed');
    Lines.Add('');
    Lines.Add('Click Next to continue.');
    PreflightMemo.Lines.Assign(Lines);
  finally
    Lines.Free;
  end;
end;

function IsComponentSelected(const Id: string): Boolean;
var
  I: Integer;
  S: String;
begin
  Result := False;
  if not Assigned(WizardForm) then Exit;
  for I := 0 to WizardForm.ComponentsList.Items.Count - 1 do
  begin
    if not WizardForm.ComponentsList.Checked[I] then Continue;
    S := WizardForm.ComponentsList.Items[I];
    if Pos('<' + Id + '>', S) > 0 then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

function ShouldInstallPython: Boolean;
begin
  Result := IsComponentSelected('python') and (not PythonDetected);
end;

function ShouldInstallVCRedist: Boolean;
begin
  Result := IsComponentSelected('vcredist') and (not VCRedistDetected);
end;

function AddFirewallRule(Port: Integer; const Protocol: string): Boolean;
var
  Script, OutStr: string;
begin
  Script :=
    'netsh advfirewall firewall delete rule name="' + APP_FIREWALL_RULE_NAME +
    '" protocol=' + Protocol + ' localport=' + IntToStr(Port) + ' | Out-Null; ' +
    'netsh advfirewall firewall add rule name="' + APP_FIREWALL_RULE_NAME +
    ' (' + Protocol + '/' + IntToStr(Port) + ')" ' +
    'dir=in action=allow protocol=' + Protocol + ' localport=' + IntToStr(Port) +
    ' profile=any';
  RunPowerShell(Script, OutStr);
  Result := Pos('Ok.', OutStr) > 0;
end;

function ConfigureFirewallRule(Port: Integer; out Memo: string): Boolean;
begin
  if not ShouldConfigureFirewall then
  begin
    Memo := 'skipped (user opted out)';
    Result := False;
    Exit;
  end;
  if AddFirewallRule(Port, 'TCP') then
  begin
    Memo := 'TCP/' + IntToStr(Port) + ' inbound ALLOW';
    Result := True;
  end
  else
  begin
    Memo := 'TCP/' + IntToStr(Port) + ' rule could not be added (admin required)';
    Result := False;
  end;
end;

procedure CopyConfiguration;
var
  DestDir: string;
  Manifest: AnsiString;
begin
  DestDir := ExpandConstant('{commondocs}\' + APP_DATA_DIR_NAME);
  ForceDirectories(DestDir);
  ForceDirectories(DestDir + '\config');
  ForceDirectories(DestDir + '\data');
  ForceDirectories(DestDir + '\logs');
  ForceDirectories(DestDir + '\backups');
  Manifest :=
    '{' + #13#10 +
    '  "version": "' + ExpandConstant('{#AppVersion}') + '",' + #13#10 +
    '  "installed_at": "' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0) + '",' + #13#10 +
    '  "install_path": "' + ExpandConstant('{app}') + '",' + #13#10 +
    '  "data_path": "' + DestDir + '",' + #13#10 +
    '  "publisher": "' + ExpandConstant('{#MyAppPublisher}') + '"' + #13#10 +
    '}';
  SaveStringToFile(DestDir + '\install.json', Manifest, False);
end;

function VerifyInstallation: TArrayOfString;
var
  Checks: TArrayOfString;
  Exe, AppDir: string;
begin
  SetArrayLength(Checks, 16);
  AppDir := ExpandConstant('{app}');
  Checks[0] := 'Application directory exists';
  if DirExists(AppDir) then Checks[1] := 'PASS' else Checks[1] := 'FAIL';

  Checks[2] := 'AIClusterMaster.exe present';
  Exe := AppDir + '\master\AIClusterMaster.exe';
  if FileExists(Exe) then Checks[3] := 'PASS' else Checks[3] := 'FAIL: ' + Exe;

  Checks[4] := 'AIClusterWorker.exe present';
  Exe := AppDir + '\worker\AIClusterWorker.exe';
  if FileExists(Exe) then Checks[5] := 'PASS' else Checks[5] := 'WARN (optional)';

  Checks[6] := 'AIClusterStudio.exe present';
  Exe := AppDir + '\studio\AIClusterStudio.exe';
  if FileExists(Exe) then Checks[7] := 'PASS' else Checks[7] := 'WARN (optional)';

  Checks[8] := 'aicluster.exe present';
  Exe := AppDir + '\cli\aicluster.exe';
  if FileExists(Exe) then Checks[9] := 'PASS' else Checks[9] := 'WARN (optional)';

  Checks[10] := 'Configuration copied to data dir';
  if FileExists(ExpandConstant('{commondocs}\' + APP_DATA_DIR_NAME) + '\install.json') then
    Checks[11] := 'PASS'
  else
    Checks[11] := 'FAIL';

  Checks[12] := 'Visual C++ runtime available';
  if DetectVC2015Plus then
    Checks[13] := 'PASS'
  else
    Checks[13] := 'WARN (not installed)';

  Checks[14] := 'Python 3.12+ available';
  if PythonDetected then
    Checks[15] := 'PASS'
  else
    Checks[15] := 'WARN (not installed)';

  Result := Checks;
end;

procedure RefreshVerify;
var
  Checks: TArrayOfString;
  Lines: TStringList;
  I, Count, Failed: Integer;
begin
  Checks := VerifyInstallation;
  Count := GetArrayLength(Checks);
  Failed := 0;
  Lines := TStringList.Create;
  try
    Lines.Add('Verification report');
    Lines.Add('==================');
    Lines.Add('');
    I := 0;
    while I < Count do
    begin
      Lines.Add(' - ' + Checks[I]);
      Lines.Add('   ' + Checks[I + 1]);
      if Pos('FAIL', Checks[I + 1]) = 1 then Failed := Failed + 1;
      I := I + 2;
    end;
    Lines.Add('');
    if Failed = 0 then
      Lines.Add('All checks passed. AICluster is ready to launch.')
    else
      Lines.Add(IntToStr(Failed) + ' check(s) failed. Review the report.');
    VerifyMemo.Lines.Assign(Lines);
    if Failed = 0 then
      VerifyStatus.Caption := 'Verification PASSED'
    else
      VerifyStatus.Caption := 'Verification FAILED (' + IntToStr(Failed) + ' failures)';
  finally
    Lines.Free;
  end;
end;

procedure InitializeWizard;
begin
  SetArrayLength(APP_FIREWALL_PORTS, 5);
  APP_FIREWALL_PORTS[0] := 8000;
  APP_FIREWALL_PORTS[1] := 8001;
  APP_FIREWALL_PORTS[2] := 5174;
  APP_FIREWALL_PORTS[3] := 5175;
  APP_FIREWALL_PORTS[4] := 1420;

  PythonDetected := False;
  VCRedistDetected := False;
  ShouldConfigureFirewall := True;
  ShouldLaunchMaster := True;

  // --- Preflight page ----------------------------------------------------
  PreflightPage := CreateCustomPage(wpWelcome,
    ExpandConstant('{cm:PreflightTitle}'), ExpandConstant('{cm:PreflightLabel}'));
  PreflightMemo := TMemo.Create(PreflightPage);
  PreflightMemo.Parent := PreflightPage.Surface;
  PreflightMemo.SetBounds(0, 0, PreflightPage.SurfaceWidth,
    PreflightPage.SurfaceHeight - 60);
  PreflightMemo.ReadOnly := True;
  PreflightMemo.ScrollBars := ssVertical;
  PreflightMemo.Font.Name := 'Consolas';
  PreflightMemo.Font.Size := 9;
  PreflightStatus := TNewStaticText.Create(PreflightPage);
  PreflightStatus.Parent := PreflightPage.Surface;
  PreflightStatus.SetBounds(0, PreflightPage.SurfaceHeight - 50,
    PreflightPage.SurfaceWidth, 20);
  PreflightStatus.Caption := 'Click Rescan to re-check the system.';
  PreflightRescanButton := TButton.Create(PreflightPage);
  PreflightRescanButton.Parent := PreflightPage.Surface;
  PreflightRescanButton.SetBounds(0, PreflightPage.SurfaceHeight - 28, 120, 24);
  PreflightRescanButton.Caption := 'Rescan';
  PreflightRescanButton.OnClick := @RefreshPreflight;
  RefreshPreflight(nil);

  // --- Firewall page -----------------------------------------------------
  FirewallPage := CreateCustomPage(PreflightPage.ID,
    ExpandConstant('{cm:FirewallTitle}'), ExpandConstant('{cm:FirewallLabel}'));
  FirewallCheck := TCheckBox.Create(FirewallPage);
  FirewallCheck.Parent := FirewallPage.Surface;
  FirewallCheck.SetBounds(0, 0, FirewallPage.SurfaceWidth, 24);
  FirewallCheck.Checked := True;
  FirewallCheck.Caption := 'Register Windows Firewall inbound rules for AICluster ports';

  // --- Verify page -------------------------------------------------------
  VerifyPage := CreateCustomPage(wpInstalling,
    ExpandConstant('{cm:VerifyTitle}'), ExpandConstant('{cm:VerifyLabel}'));
  VerifyMemo := TMemo.Create(VerifyPage);
  VerifyMemo.Parent := VerifyPage.Surface;
  VerifyMemo.SetBounds(0, 0, VerifyPage.SurfaceWidth, VerifyPage.SurfaceHeight - 30);
  VerifyMemo.ReadOnly := True;
  VerifyMemo.ScrollBars := ssVertical;
  VerifyMemo.Font.Name := 'Consolas';
  VerifyMemo.Font.Size := 9;
  VerifyStatus := TNewStaticText.Create(VerifyPage);
  VerifyStatus.Parent := VerifyPage.Surface;
  VerifyStatus.SetBounds(0, VerifyPage.SurfaceHeight - 24,
    VerifyPage.SurfaceWidth, 20);
  VerifyStatus.Caption := 'Waiting for installation to finish...';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  I, Port: Integer;
  Memo: string;
  AllOk: Boolean;
  Lines: TStringList;
begin
  Result := True;
  if CurPageID = FirewallPage.ID then
  begin
    ShouldConfigureFirewall := FirewallCheck.Checked;
    if not ShouldConfigureFirewall then Exit;
    AllOk := True;
    Lines := TStringList.Create;
    try
      Lines.Add('Firewall configuration');
      Lines.Add('======================');
      Lines.Add('');
      for I := 0 to GetArrayLength(APP_FIREWALL_PORTS) - 1 do
      begin
        Port := APP_FIREWALL_PORTS[I];
        if ConfigureFirewallRule(Port, Memo) then
          Lines.Add('[OK]   ' + Memo)
        else
        begin
          Lines.Add('[WARN] ' + Memo);
          AllOk := False;
        end;
      end;
      Log(Lines.Text);
    finally
      Lines.Free;
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = VerifyPage.ID then
  begin
    CopyConfiguration;
    RefreshVerify;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // Final handoff. The launch preference is handled by the standard
  // [Run] entry's "FinishedRun" checkbox; nothing extra to do here.
end;

function UpdateReadyMemo(const Space, NewLine, MemoUserInfoInfo, MemoDirInfo,
  MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: string): string;
begin
  Result :=
    'AICluster will be installed to:' + NewLine +
    Space + MemoDirInfo + NewLine + NewLine +
    'AICluster data will be stored in:' + NewLine +
    Space + ExpandConstant('{commondocs}\' + APP_DATA_DIR_NAME) + NewLine + NewLine +
    MemoComponentsInfo + NewLine +
    MemoTasksInfo;
end;
