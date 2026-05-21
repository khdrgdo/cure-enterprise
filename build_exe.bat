@echo off
title Building Cure Enterprise EXE...
cd /d "%~dp0"
echo Building Cure Enterprise executable...
pyinstaller --onefile --windowed --name "Cure_Enterprise" --add-data "assets;assets" "Cure_Enterprise_Pro.py"
echo.
echo ✅ Done! Find the .exe in the dist\ folder.
pause
