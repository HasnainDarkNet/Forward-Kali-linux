@echo off
echo Installing watchdog...
pip install watchdog >nul 2>&1
if errorlevel 1 (
    echo Failed to install watchdog. Installing with --user...
    pip install watchdog --user
)
echo Starting application...
start /B pythonw "%~dp0window.py"
exit
