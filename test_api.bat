@echo off
chcp 65001 >nul

REM API测试工具启动脚本

REM 检查是否存在虚拟环境
if exist .venv\Scripts\python.exe (
    echo 找到虚拟环境，使用虚拟环境中的Python...
    set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
    echo 使用系统Python...
    set "PYTHON_CMD=python"
)

REM 检查Python是否可用
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python。请先安装Python 3.9或更高版本。
    pause
    exit /b 1
)

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM 检查是否提供了DWG文件路径
if "%~1" neq "" (
    echo 测试DWG到PDF转换功能，文件：%~1
    %PYTHON_CMD% test_api.py "%~1"
) else (
    echo 测试API连接...
    %PYTHON_CMD% test_api.py
)

pause