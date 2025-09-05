@echo off
REM Basic dependency installation script (English only to avoid encoding issues)

cls
echo ===================================================
echo INSTALLING DEPENDENCIES FOR DWG to PDF CONVERTER API
echo Special handling for win32com dependency
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
echo 4. Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

if %errorlevel% neq 0 (
echo WARNING: Failed to upgrade pip, but continuing.
)

echo.
echo 5. Installing pywin32 (provides win32com.client)...
pip install pywin32==305

if %errorlevel% neq 0 (
echo ERROR: Failed to install pywin32!
echo Please try manual installation:
echo 1. Open Command Prompt
echo 2. Run: .venv\Scripts\activate.bat
echo 3. Run: pip install pywin32
pause
exit /b 1
)

echo.
echo 6. Installing other dependencies...
pip install fastapi uvicorn python-multipart pyautocad reportlab

if %errorlevel% neq 0 (
echo WARNING: Some dependencies may have failed, but checking main components.
)

echo.
echo 7. Verifying win32com installation...
python -c "import win32com.client; import pythoncom; print('OK: win32com.client and pythoncom imported successfully!')"

if %errorlevel% neq 0 (
echo ERROR: Failed to import win32com.client!
echo Try these solutions:
echo 1. Check if you're using 32-bit or 64-bit Python, match with AutoCAD version
echo 2. Reinstall pywin32: pip uninstall pywin32 && pip install pywin32
echo 3. Check for multiple Python version conflicts
pause
exit /b 1
)

echo.
echo 8. Verifying other key dependencies...
python -c "import fastapi; import uvicorn; print('OK: FastAPI and Uvicorn imported successfully!')"

echo.
echo ===================================================
echo INSTALLATION COMPLETE!
echo The win32com dependency issue should be resolved.
echo You can now run start_server.bat to start the API server.
echo ===================================================

pause