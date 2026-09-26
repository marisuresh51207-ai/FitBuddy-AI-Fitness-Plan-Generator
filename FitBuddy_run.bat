@echo off
setlocal EnableExtensions

title FitBuddy - Local Server

REM Run from the folder containing this BAT file.
cd /d "%~dp0"

echo.
echo ==========================================
echo        FitBuddy - Starting Project
echo ==========================================
echo.

REM 1. Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Install Python 3.10+ and try again.
    echo.
    pause
    exit /b 1
)

REM 2. Create virtual environment if it does not exist
if not exist "venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    python -m venv venv

    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment already exists.
)

set "VENV_PY=%~dp0venv\Scripts\python.exe"

REM 3. Install dependencies on first run
if not exist "venv\.fitbuddy_dependencies_installed" (
    echo [2/4] Installing dependencies...
    "%VENV_PY%" -m pip install --disable-pip-version-check -r requirements.txt

    if errorlevel 1 (
        echo.
        echo [ERROR] Dependency installation failed.
        echo Check your internet connection and requirements.txt.
        pause
        exit /b 1
    )

    type nul > "venv\.fitbuddy_dependencies_installed"
) else (
    echo [2/4] Dependencies already installed.
)

REM 4. Check .env
if not exist ".env" (
    echo.
    echo [WARNING] .env was not found.
    echo Create a .env file in this folder containing:
    echo GEMINI_API_KEY=YOUR_GEMINI_API_KEY
    echo.
    pause
    exit /b 1
)

echo [3/4] Starting FastAPI...
echo.

REM Run Uvicorn in a separate window so this script can open Chrome.
start "FitBuddy FastAPI Server" cmd /k ""%VENV_PY%" -m uvicorn app.main:app --reload"

REM Give the server a few seconds to start.
timeout /t 3 /nobreak >nul

echo [4/4] Opening FitBuddy in Google Chrome...
echo.

set "CHROME="

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
)

if defined CHROME (
    start "" "%CHROME%" "http://127.0.0.1:8000/"
) else (
    echo Chrome was not found. Opening your default browser...
    start "" "http://127.0.0.1:8000/"
)

echo.
echo ==========================================
echo FitBuddy:
echo http://127.0.0.1:8000/
echo.
echo API Docs:
echo http://127.0.0.1:8000/docs
echo ==========================================
echo.
echo Keep the "FitBuddy FastAPI Server" window open.
echo.

endlocal
exit /b 0
