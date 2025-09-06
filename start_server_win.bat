@echo off
chcp 65001 >nul

REM DWG to PDF Converter API启动脚本 - Windows兼容版

REM 检查是否存在虚拟环境
if exist ".venv\Scripts\python.exe" (
    echo 找到虚拟环境，使用虚拟环境中的Python...
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
    set "UV_CMD=.venv\Scripts\uv.exe"
    set "UVICORN_CMD=.venv\Scripts\uvicorn.exe"
) else (
    echo 使用系统Python...
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
    set "UV_CMD=uv"
    set "UVICORN_CMD=uvicorn"
)

REM 检查Python是否可用
%PYTHON_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python。请先安装Python 3.9或更高版本。
    pause
    exit /b 1
)

REM 如果没有虚拟环境，创建一个
if not exist ".venv\Scripts\python.exe" (
    echo 创建虚拟环境...
    %PYTHON_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo 错误：创建虚拟环境失败。
        pause
        exit /b 1
    )
    
    REM 重新设置虚拟环境中的命令路径
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PIP_CMD=.venv\Scripts\pip.exe"
    set "UV_CMD=.venv\Scripts\uv.exe"
    set "UVICORN_CMD=.venv\Scripts\uvicorn.exe"
)

REM 安装依赖
if exist "requirements.txt" (
    echo 安装项目依赖...
    %PIP_CMD% install -r requirements.txt
    if %errorlevel% neq 0 (
        echo 错误：安装依赖失败。
        pause
        exit /b 1
    )
)

if exist "pyproject.toml" (
    echo 使用uv安装项目...
    %PYTHON_CMD% -m pip install --upgrade pip
    %PYTHON_CMD% -m pip install uv
    %UV_CMD% pip install -e .
    if %errorlevel% neq 0 (
        echo 错误：使用uv安装项目失败，尝试使用pip...
        %PIP_CMD% install -e .
        if %errorlevel% neq 0 (
            echo 错误：安装项目失败。
            pause
            exit /b 1
        )
    )
)

REM 创建临时目录（如果不存在）
if not exist "temp" mkdir temp

REM 启动API服务器
set "HOST=0.0.0.0"
set "PORT=8000"

echo 启动DWG to PDF Converter API服务器...
echo 服务器地址: http://%HOST%:%PORT%
%UVICORN_CMD% main:app --host %HOST% --port %PORT% --reload

if %errorlevel% neq 0 (
    echo 错误：API服务器启动失败。
    pause
    exit /b 1
)

pause