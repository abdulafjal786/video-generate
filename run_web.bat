@echo off
REM Starts the StickVoice Studio web app at http://127.0.0.1:7860
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call setup.bat
".venv\Scripts\python.exe" -m stickvoice --web
pause
