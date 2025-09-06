@echo off

REM DWG to PDF Converter API - Using UV for dependency management

REM Set paths
set "VENV_DIR=.venv"
set "PYTHON_VENV=%VENV_DIR%\Scripts\python.exe"
set "PIP_VENV=%VENV_DIR%\Scripts\pip.exe"
set "UV_VENV=%VENV_DIR%\Scripts\uv.exe"

REM Check if Python is available
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

REM Create virtual environment if not exists
if not exist "%PYTHON_VENV%" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Install UV using virtual environment's pip
echo Installing UV package manager...
"%PIP_VENV%" install --upgrade pip
"%PIP_VENV%" install uv
if %errorlevel% neq 0 (
    echo Error: Failed to install UV
    pause
    exit /b 1
)

REM Install project dependencies using UV
echo Installing project dependencies with UV...
if exist "pyproject.toml" (
    "%UV_VENV%" pip install -e .
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies from pyproject.toml
        pause
        exit /b 1
    )
)

if exist "requirements.txt" (
    "%UV_VENV%" pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies from requirements.txt
        pause
        exit /b 1
    )
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