@echo off
REM Make a video straight from the command line.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call setup.bat
set /p PROMPT="Type your video prompt: "
set /p STYLE="Style [a1-light a1-dark a2-tech a2-story a3-cave a4-cozy a5-edo a5-egypt a5-rome a6-amber b1-notebook b2-paper] (Enter = b1-notebook): "
if "%STYLE%"=="" set "STYLE=b1-notebook"
set /p RATIO="Shape [16:9 / 9:16 / 1:1] (Enter = 16:9): "
if "%RATIO%"=="" set "RATIO=16:9"
".venv\Scripts\python.exe" -m stickvoice "%PROMPT%" --style %STYLE% --ratio %RATIO%
echo.
echo Your video is in the output folder.
start "" "%~dp0output"
pause
