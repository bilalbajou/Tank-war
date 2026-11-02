; Script Inno Setup pour Tank War : Arena Duel
; Permet de générer TankWar_Setup_v1.0.exe

#define MyAppName "Tank War : Arena Duel"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Arena Duel Team"
#define MyAppURL "https://github.com"
#define MyAppExeName "TankWar.exe"

[Setup]
AppId={{8B17C8A9-2A5F-4E38-9B5C-2D3B89E28B10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\TankWar
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=TankWar_Setup_v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\TankWar\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\TankWar\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

