@echo off
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python 3 is required. Install from https://www.python.org/downloads/
    echo Then run: pip install bcrypt
    pause
    exit /b 1
)
start "" "%~dp0GalacticFrontier.exe"
