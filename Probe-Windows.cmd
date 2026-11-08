@echo off
setlocal
set "DST=%~1"
if not defined DST set "DST=%LOCALAPPDATA%\VOCALOID6-CN-6.13.3-R1"
if defined DOTNET_STARTUP_HOOKS (echo Existing DOTNET_STARTUP_HOOKS detected. & pause & exit /b 1)
set "V6CN_TARGET_ROOT=%DST%"
set "V6CN_LOG=%DST%\V6CN-probe.log"
set "DOTNET_STARTUP_HOOKS=%DST%\V6CN.StartupHook.dll"
dotnet exec --runtimeconfig "%DST%\VOCALOID6.runtimeconfig.json" "%~dp0payload\toolkit\V6CN.Toolkit.dll" probe "%DST%" "%DST%\Windows-resource-probe.json" --hook
if errorlevel 1 (echo Resource probe failed. & pause & exit /b 1)
echo Resource checks passed. Complete the Windows UI checklist before accepting the patch.
pause
