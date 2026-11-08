@echo off
setlocal
set "DST=%~1"
if not defined DST set "DST=%LOCALAPPDATA%\VOCALOID6-CN-6.13.3-R1"
dotnet "%~dp0payload\toolkit\V6CN.Toolkit.dll" restore "%DST%"
if errorlevel 1 (echo Restore failed. Read the error above. & pause & exit /b 1)
pause
