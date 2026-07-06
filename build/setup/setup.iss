; AICluster v2.0 Setup — Native Windows Desktop Installer

#define MyAppName "AICluster"
#define MyAppPublisher "AICluster"
#define MyAppURL "https://aicluster.local"
#define MyAppId "com.aicluster.studio"

#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#ifndef AppSourceDir
  #define AppSourceDir "payload\aicluster"
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
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=AIClusterSetup-{#AppVersion}
SetupIconFile=..\..\assets\icons\default.ico
UninstallDisplayIcon={app}\studio\AIClusterStudio.exe
Compression=lzma2/ultra64
SolidCompression=no
WizardStyle=modern
WizardSizePercent=120
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=AICluster {#AppVersion} Setup
UninstallDisplayName={#MyAppName} {#AppVersion}
UninstallFilesDir={app}\uninst
AppMutex=AIClusterStudioMutex,Global\AIClusterStudioMutex

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "firewall"; Description: "Allow AICluster through &Windows Firewall"; GroupDescription: "Network:"

[Files]
; Studio desktop application
Source: "{#AppSourceDir}\studio\*"; DestDir: "{app}\studio"; Flags: ignoreversion recursesubdirs createallsubdirs

; Combined runtime (Master + Worker + CLI in one EXE)
Source: "{#AppSourceDir}\runtime\*"; DestDir: "{app}\runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration
Source: "..\..\config\default.yaml"; DestDir: "{app}\config"; Flags: ignoreversion

; Assets
Source: "..\..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Licenses
Source: "..\..\release\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\runtime"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\models"; Permissions: users-modify
Name: "{app}\plugins"; Permissions: users-modify
Name: "{app}\cache"; Permissions: users-modify
Name: "{app}\updates"; Permissions: users-modify
Name: "{app}\temp"; Permissions: users-modify
Name: "{app}\config"; Permissions: users-modify

[Icons]
Name: "{group}\AICluster Studio"; Filename: "{app}\studio\AIClusterStudio.exe"; WorkingDir: "{app}"; Comment: "AICluster Studio"
Name: "{group}\Uninstall AICluster"; Filename: "{uninstallexe}"
Name: "{commondesktop}\AICluster Studio"; Filename: "{app}\studio\AIClusterStudio.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\runtime\AIClusterRuntime.exe"; Parameters: "--mode master"; WorkingDir: "{app}\runtime"; Description: "Starting AICluster Master Server..."; Flags: postinstall nowait skipifsilent runhidden
Filename: "{app}\studio\AIClusterStudio.exe"; Description: "Launch AICluster Studio after installation"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{app}\updates"
Type: filesandordirs; Name: "{app}\logs"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  rc: Integer;
  rolePath, roleContent: String;
begin
  if CurStep = ssPostInstall then
  begin
    rolePath := ExpandConstant('{app}\config\role.json');
    roleContent := '{"role":"standalone","configured":true,"version":"{#AppVersion}","settings":{"master_host":"127.0.0.1","master_port":8000,"worker_port":8001,"worker_master_url":null,"worker_name":null}}';
    if not SaveStringToFile(rolePath, roleContent, False) then
      Log('WARNING: Could not write role.json to ' + rolePath);

    if WizardIsTaskSelected('firewall') then
    begin
      Exec('netsh', 'advfirewall firewall add rule name="AICluster Runtime" dir=in action=allow program="' + ExpandConstant('{app}') + '\runtime\AIClusterRuntime.exe" enable=yes profile=private', '', SW_HIDE, ewNoWait, rc);
    end;
  end;
end;

function InitializeUninstall: Boolean;
var
  rc: Integer;
begin
  Exec('netsh', 'advfirewall firewall delete rule name="AICluster Runtime"', '', SW_HIDE, ewWaitUntilTerminated, rc);
  Result := True;
end;
