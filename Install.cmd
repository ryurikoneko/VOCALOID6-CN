@echo off
setlocal
cd /d "%~dp0"
where dotnet >nul 2>nul
if errorlevel 1 (echo .NET 8 is required. Install the Microsoft .NET 8 Desktop Runtime. & pause & exit /b 1)
set "SRC=%~1"
if not defined SRC if exist "%ProgramFiles%\VOCALOID6\Editor\VOCALOID6.dll" set "SRC=%ProgramFiles%\VOCALOID6\Editor"
if not defined SRC set /p "SRC=Original VOCALOID6 Editor directory: "
set "DST=%~2"
if not defined DST set "DST=%LOCALAPPDATA%\VOCALOID6-CN-6.13.3-R1"
dotnet "%~dp0payload\toolkit\V6CN.Toolkit.dll" install "%SRC%" "%DST%"
if errorlevel 1 (echo Installation failed. Read the error above. & pause & exit /b 1)
echo Start the Chinese copy using:
echo %DST%\Start-Chinese.cmd
pause
