[Setup]
AppName=Vidpull
AppVersion=1.0.0
AppPublisher=Vidpull
DefaultDirName={autopf}\Vidpull
DefaultGroupName=Vidpull
OutputDir=installer_output
OutputBaseFilename=Vidpull_Setup
SetupIconFile=logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Vidpull.exe
PrivilegesRequired=admin
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\Vidpull\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Vidpull"; Filename: "{app}\Vidpull.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\Uninstall Vidpull"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Vidpull"; Filename: "{app}\Vidpull.exe"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Vidpull.exe"; Description: "Launch Vidpull"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
