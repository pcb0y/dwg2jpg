@echo off
chcp 65001 >nul

REM 修复DWG to PDF Converter API依赖问题

REM 检查是否存在虚拟环境
if exist .venv\Scripts\python.exe (
    echo 找到虚拟环境，使用虚拟环境中的Python...
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
) else (
    echo 使用系统Python...
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

REM 检查Python是否可用
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python。请先安装Python 3.9或更高版本。
    pause
    exit /b 1
)

REM 如果没有虚拟环境，创建一个
if not exist .venv\Scripts\python.exe (
    echo 创建虚拟环境...
    %PYTHON_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo 错误：创建虚拟环境失败。
        pause
        exit /b 1
    )
    
    REM 更新环境变量以使用新创建的虚拟环境
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 升级pip
call .venv\Scripts\python.exe -m pip install --upgrade pip

REM 安装pywin32（修复win32com.client导入问题）
call .venv\Scripts\pip.exe install pywin32

REM 安装其他依赖
call .venv\Scripts\pip.exe install fastapi uvicorn python-multipart pyautocad reportlab

REM 验证安装
call .venv\Scripts\python.exe -c "import win32com.client; print('✅ win32com.client 导入成功')"
call .venv\Scripts\python.exe -c "import fastapi; print('✅ fastapi 导入成功')"
call .venv\Scripts\python.exe -c "import uvicorn; print('✅ uvicorn 导入成功')"
call .venv\Scripts\python.exe -c "import pythoncom; print('✅ pythoncom 导入成功')"

echo.
echo ==================================================
echo 依赖修复完成！
echo 如果看到所有✅标记，表示依赖已成功安装。
echo 现在可以尝试运行 start_server.bat 启动API服务器。
echo ==================================================

pause