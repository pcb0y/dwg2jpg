@echo off

REM Basic UV-based startup script - Skip project build

REM Check Python availability
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Install UV globally
pip install uv --upgrade
if %errorlevel% neq 0 (
    echo Error: Failed to install UV globally
    pause
    exit /b 1
)

REM Create virtual environment
uv venv .venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

REM Install required packages using UV
echo Installing required packages...
uv pip install fastapi uvicorn python-multipart reportlab pyodbc python-dotenv

REM Create temp directory if not exists
if not exist temp mkdir temp

REM Start server
echo Starting API server...
echo Server address: http://localhost:8000
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

if %errorlevel% neq 0 (
    echo Error: Failed to start server
    pause
    exit /b 1
)

pause