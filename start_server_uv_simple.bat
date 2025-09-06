@echo off

REM Simplified startup script using UV for dependency management

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

REM Use UV to create/update virtual environment
uv venv .venv
if %errorlevel% neq 0 (
    echo Error: Failed to create/update virtual environment with UV
    pause
    exit /b 1
)

REM Install dependencies using UV
if exist "pyproject.toml" (
    uv pip install -e .
)

if exist "requirements.txt" (
    uv pip install -r requirements.txt
)

REM Create temp directory
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