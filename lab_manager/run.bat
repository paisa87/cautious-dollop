@echo off
REM ─────────────────────────────────────────────
REM  VG Lab Manager — Windows launcher
REM ─────────────────────────────────────────────

cd /d "%~dp0"

echo.
echo   VG Lab Manager - Starting up...
echo.

REM Check Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo   ERROR: Python is not installed or not in PATH.
    echo   Download it from https://www.python.org/downloads/
    echo   Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
IF NOT EXIST "venv\" (
    echo   First-time setup: creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install/update dependencies
echo   Checking dependencies...
pip install -q -r requirements.txt

echo.
echo   Ready! Open your browser to:  http://localhost:5000
echo.
echo   Default login:  username = admin   password = labadmin
echo   ^(Change the password after your first login!^)
echo.
echo   Press Ctrl+C to stop the server.
echo.

REM Open browser
start "" "http://localhost:5000"

python app.py
pause
