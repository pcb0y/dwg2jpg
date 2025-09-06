@echo off

REM DWG to PDF Converter API - Reliable Startup Script

REM Set paths using Windows format
set "VENV_DIR=.venv"
set "PYTHON_VENV=%VENV_DIR%\Scripts\python.exe"
set "PIP_VENV=%VENV_DIR%\Scripts\pip.exe"

REM Check if virtual environment exists, create if not
if not exist "%PYTHON_VENV%" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Install requirements using virtual environment's pip
echo Installing dependencies...
"%PIP_VENV%" install --upgrade pip
"%PIP_VENV%" install fastapi uvicorn python-multipart
if exist "requirements.txt" (
    "%PIP_VENV%" install -r requirements.txt
)

REM Create temp directory if not exists
if not exist temp mkdir temp

REM Start server using virtual environment's Python
echo Starting API server...
echo Server will be available at http://localhost:8000
"%PYTHON_VENV%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

if %errorlevel% neq 0 (
    echo Error: Failed to start server
    pause
    exit /b 1
)

pause