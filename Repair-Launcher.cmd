@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Repair-Launcher.ps1" %*
set "V6CN_REPAIR_EXIT=%errorlevel%"
pause
exit /b %V6CN_REPAIR_EXIT%
