@echo off
REM Simple API test script (English only to avoid encoding issues)

cls
echo ===================================================
 echo TESTING DWG to PDF CONVERTER API
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
echo 4. Installing required dependencies for testing...
pip install requests >nul 2>&1


echo.
echo 5. Testing API...
REM Check if a DWG file path was provided
if "%~1" neq "" (
echo Testing DWG to PDF conversion with file: %~1
python test_api.py "%~1"
) else (
echo Testing API connection...
python test_api.py
)

pause