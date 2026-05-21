# Install Cure Enterprise
# Run as Administrator
param([switch]$Silent)

$AppName = "Cure Enterprise"
$SourceDir = Join-Path $PSScriptRoot "dist\Cure_Enterprise"
$TargetDir = Join-Path $env:ProgramFiles $AppName
$StartMenu = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\$AppName"
$Desktop = [Environment]::GetFolderPath("Desktop")

$Shell = New-Object -ComObject WScript.Shell

# Elevate self
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    $args = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($Silent) { $args += " -Silent" }
    Start-Process powershell -Verb RunAs -ArgumentList $args
    exit
}

Write-Host "Installing $AppName ..."

# Kill running instance
Get-Process -Name "Cure_Enterprise" -ErrorAction SilentlyContinue | Stop-Process -Force

# Clean old
if (Test-Path $TargetDir) { Remove-Item -Recurse -Force $TargetDir }
New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

# Copy files
Write-Host "Copying files ..."
Copy-Item -Recurse -Force "$SourceDir\*" $TargetDir

# Start Menu
if (Test-Path $StartMenu) { Remove-Item -Recurse -Force $StartMenu }
New-Item -ItemType Directory -Path $StartMenu -Force | Out-Null

$sc = $Shell.CreateShortcut("$StartMenu\$AppName.lnk")
$sc.TargetPath = "$TargetDir\Cure_Enterprise.exe"
$sc.WorkingDirectory = $TargetDir
$sc.Save()

# Desktop shortcut
$sc = $Shell.CreateShortcut("$Desktop\$AppName.lnk")
$sc.TargetPath = "$TargetDir\Cure_Enterprise.exe"
$sc.WorkingDirectory = $TargetDir
$sc.Save()

# Uninstall script
$uni = @'
# Uninstall Cure Enterprise
$d = "$TargetDir"
Get-Process "Cure_Enterprise" -ErrorAction SilentlyContinue | Stop-Process -Force
Remove-Item -Recurse -Force $d -ErrorAction SilentlyContinue
$sm = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\$AppName"
Remove-Item -Recurse -Force $sm -ErrorAction SilentlyContinue
$dk = [Environment]::GetFolderPath("Desktop")
Remove-Item -Force "$dk\$AppName.lnk" -ErrorAction SilentlyContinue
Write-Host "Uninstalled"
'@ -replace '\$TargetDir', $TargetDir -replace '\$AppName', $AppName
$uni | Out-File -FilePath "$TargetDir\uninstall.ps1" -Encoding utf8

Write-Host "Done! Installed to: $TargetDir" -ForegroundColor Green
Write-Host "Desktop shortcut created." -ForegroundColor Green

# Ask to run
if (-not $Silent) {
    $run = $Shell.Popup("Run $AppName now?", 0, "Install Complete", 4+32)
    if ($run -eq 6) { Start-Process "$TargetDir\Cure_Enterprise.exe" }
}
