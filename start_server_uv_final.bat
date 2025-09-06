@echo off

REM Simplified UV-based startup script - Skip virtual environment

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

REM Install all required dependencies using UV
echo Installing all required dependencies...
uv pip install fastapi uvicorn python-multipart reportlab pyodbc python-dotenv ezdxf

REM Create temp directory
if not exist temp mkdir temp

REM Start server directly
echo Starting API server...
echo Server address: http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

if %errorlevel% neq 0 (
    echo Error: Failed to start server
    pause
    exit /b 1
)

pause