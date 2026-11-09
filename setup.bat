@echo off
REM One-time setup: creates .venv and installs Python packages (ffmpeg is included via imageio-ffmpeg).
cd /d "%~dp0"
set "PY=python"
where py >nul 2>nul && set "PY=py -3"
%PY% --version >nul 2>nul || (echo Python 3.9+ is required. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH". & pause & exit /b 1)
if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (echo Setup failed. & pause & exit /b 1)
echo.
echo Setup complete. Double-click run_web.bat to start StickVoice Studio.
pause
