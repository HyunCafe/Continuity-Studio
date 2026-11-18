@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0Support\host.py" (
  echo Continuity Studio source files were not found.
  pause
  exit /b 1
)
where pyw >nul 2>nul
if not errorlevel 1 (
  start "" pyw -3 "%~dp0Support\host.py" --demo
  exit /b 0
)
where py >nul 2>nul
if not errorlevel 1 (
  start "" py -3 "%~dp0Support\host.py" --demo
  exit /b 0
)
echo Python 3 is needed for the app-window preview.
echo For an interface-only preview, open GUI\index.html directly.
pause
exit /b 1
