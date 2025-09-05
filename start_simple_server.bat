@echo off
REM Simple server start script (English only to avoid encoding issues)
REM Uses pip instead of uv for dependency installation

cls
echo ===================================================
echo STARTING DWG to PDF CONVERTER API SERVER
===================================================

echo.

echo 1. Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
echo ERROR: Python not found. Please install Python 3.9 or higher first.
pause
exit /b 1
)

echo.
echo 2. Checking virtual environment...
if not exist .venv (
echo Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
echo ERROR: Failed to create virtual environment.
pause
exit /b 1
)
) else (
echo Virtual environment already exists
)

echo.
echo 3. Activating virtual environment...
call .venv\Scripts\activate.bat

if %errorlevel% neq 0 (
echo ERROR: Failed to activate virtual environment.
pause
exit /b 1
)

echo.
echo 4. Checking main dependencies...
python -c "import win32com.client; import fastapi; print('Dependencies check passed')" >nul 2>&1

if %errorlevel% neq 0 (
echo WARNING: Some dependencies are missing. Installing required packages...
pip install pywin32 fastapi uvicorn python-multipart
)

echo.
echo 5. Starting API server...
echo Server will be available at http://localhost:8000
uvicorn main:app --reload

if %errorlevel% neq 0 (
echo ERROR: Failed to start the server.
pause
exit /b 1
)

pause