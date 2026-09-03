@echo off
REM Double-click launcher for colleagues who have Python installed.
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
python -m numeracycheck
if errorlevel 1 pause
