@echo off
REM Optional: installs the VoiceStudio desktop app using its official installer
REM (from https://github.com/debpalash/voicestudio README). It runs locally on port 3900.
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://voicestudio.sh/install.ps1 | iex"
pause
