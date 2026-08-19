; ============================================================
;  Subtitr Desktop — Inno Setup installer script
;  Foydalanuvchi bitta Setup.exe ni yuklab, o'rnatib ishlatadi.
;  API kalitlar dastur ichidan kiritiladi (hech narsa shart emas).
; ============================================================

#define MyAppName "Subtitr Desktop"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Subtitr"
#define MyAppExeName "subtitr_app.exe"
#define SourceDir "Subtitr-Release"

[Setup]
AppId={{B7A3F0E2-6C4D-4E9A-9F1B-2D8C5A7E3B10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Per-user install — UAC/admin talab qilmaydi, LocalAppData ga o'rnatiladi.
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=SubtitrSetup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=subtitr_app\windows\runner\resources\app_icon.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Butun tayyor paket (Flutter exe + DLL + data + desktop_processor.exe + ffmpeg/ffprobe + .env.example)
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{#MyAppName} ni o'chirish"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
