@echo off
title Cure Enterprise - نظام إدارة الصيدليات
cd /d "%~dp0"

:: Try the compiled EXE first, fallback to Python
if exist "dist\Cure_Enterprise.exe" (
    start /b "" "dist\Cure_Enterprise.exe"
) else (
    start /b pythonw "Cure_Enterprise_Pro.py"
)
exit
