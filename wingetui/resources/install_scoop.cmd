@echo off
SET wingetuipath=%~dp0..\wingetui.exe
set pwsh=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
echo Scoop Installer Assistant - WingetUI
echo This script will install Scoop and its dependencies, since it appears that they are not installed on your machine.
pause
%pwsh% Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
%pwsh% -ExecutionPolicy ByPass -File "%~dp0\install_scoop.ps1"
if %errorlevel% equ 0 (
    echo WingetUI will be restarted to continue.
    pause
    taskkill /im wingetui.exe /f
    start /b "%wingetuipath%" /i
) else (
    pause
    taskkill /im wingetui.exe /f
    start /b "%wingetuipath%" /i
)
