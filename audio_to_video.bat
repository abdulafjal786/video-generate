@echo off
REM Drag an audio file onto this .bat (or run it and type the path) to turn your recording into a stickman video.
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call setup.bat
set "AUDIO=%~1"
if "%AUDIO%"=="" set /p AUDIO="Path to your audio file: "
set /p LANG="Language code [en/hi/bn/ta/... Enter = auto]: "
set /p RATIO="Shape [16:9 / 9:16 / 1:1] (Enter = 16:9): "
if "%RATIO%"=="" set "RATIO=16:9"
set /p STYLE="Style [a1-light a1-dark a2-tech a2-story a3-cave a4-cozy a5-edo a5-egypt a5-rome a6-amber b1-notebook b2-paper] (Enter = b1-notebook): "
if "%STYLE%"=="" set "STYLE=b1-notebook"
if "%LANG%"=="" (".venv\Scripts\python.exe" -m stickvoice --audio "%AUDIO%" --ratio %RATIO% --style %STYLE%) else (".venv\Scripts\python.exe" -m stickvoice --audio "%AUDIO%" --language %LANG% --ratio %RATIO% --style %STYLE%)
echo.
echo Your video is in the output folder.
start "" "%~dp0output"
pause
