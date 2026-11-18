@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Python 3 not found.&pause&exit /b 1)
py -3 -m unittest discover -s Tests -v
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
