@echo off
REM Drag an output\<video> folder onto this file after putting clips.zip (from the Colab notebook) inside it.
REM Makes ai_video.mp4: the AI clips + StickVoice's voice and captions.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call setup.bat
if "%~1"=="" (
  echo Drag your output\^<video^> folder onto this file.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m stickvoice --assemble "%~1"
pause
