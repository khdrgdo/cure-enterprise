; Inno Setup script for Cure Enterprise
; Install Inno Setup from https://jrsoftware.org/isdl.php
; Then right-click this file → Compile (or: ISCC.exe setup.iss)

#define MyAppName "Cure Enterprise"
#define MyAppVersion "4.0"
#define MyAppPublisher "Cure"
#define MyAppURL ""
#define MyAppExeName "Cure_Enterprise.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Cure_Enterprise_Setup_v{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات:"; Flags: checkedonce

[Files]
Source: "dist\Cure_Enterprise\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Cure_Enterprise\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\إلغاء التثبيت"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('حذف مجلد قاعدة البيانات والملفات أيضًا؟', mbConfirmation, MB_YESNO) = idYes then
      DelTree(ExpandConstant('{app}\data'), True, True, True);
  end;
end;
