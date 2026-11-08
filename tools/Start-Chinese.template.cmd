@echo off
setlocal
set "V6CN_ROOT=%~dp0"
if not exist "%V6CN_ROOT%VOCALOID6.exe" goto missing
if not exist "%V6CN_ROOT%V6CN.StartupHook.dll" goto missing
if not exist "%V6CN_ROOT%zh-CN\VOCALOID6.resources.dll" goto missing
if defined DOTNET_STARTUP_HOOKS goto conflict
set "V6CN_TARGET_ROOT=%V6CN_ROOT%"
set "V6CN_LOG=%V6CN_ROOT%V6CN-runtime.log"
set "DOTNET_STARTUP_HOOKS=%V6CN_ROOT%V6CN.StartupHook.dll"
pushd "%V6CN_ROOT%"
if errorlevel 1 goto workdir
>>"%V6CN_ROOT%V6CN-launch.log" echo [%date% %time%] Starting VOCALOID6
"%V6CN_ROOT%VOCALOID6.exe" %* >>"%V6CN_ROOT%V6CN-launch.log" 2>&1
set "V6CN_EXIT=%errorlevel%"
>>"%V6CN_ROOT%V6CN-launch.log" echo [%date% %time%] Exit code: %V6CN_EXIT%
popd
if not "%V6CN_EXIT%"=="0" goto failed
exit /b 0
:missing
echo The launcher must stay in the installed Editor copy.
echo Do not move this CMD file to the desktop. Use the desktop shortcut.
echo Run Repair-Launcher.cmd to restore the launcher and create a shortcut.
pause
exit /b 2
:conflict
echo DOTNET_STARTUP_HOOKS is already set in this process.
echo Open the desktop shortcut from File Explorer, or use a fresh command prompt.
pause
exit /b 3
:workdir
echo Cannot open the Editor working directory.
pause
exit /b 4
:failed
echo VOCALOID6 exited with code %V6CN_EXIT%.
echo Diagnostic output: %V6CN_ROOT%V6CN-launch.log
type "%V6CN_ROOT%V6CN-launch.log"
pause
exit /b %V6CN_EXIT%
