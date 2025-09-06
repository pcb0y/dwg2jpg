@echo off

REM Simple startup script without Chinese characters

REM Check Python availability
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Create virtual environment if not exists
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

REM Create temp directory if not exists
if not exist temp mkdir temp

REM Start API server
echo Starting API server...
echo Server address: http://0.0.0.0:8000
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

if %errorlevel% neq 0 (
    echo Error: Failed to start API server
    pause
    exit /b 1
)

pause