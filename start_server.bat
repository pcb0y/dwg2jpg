@echo off


REM DWG to JPG Converter API启动脚本

REM 检查是否存在虚拟环境
if exist .venv\Scripts\python.exe (
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
    set "UV_CMD=.venv\Scripts\uv.exe"
    set "UVICORN_CMD=.venv\Scripts\uvicorn.exe"
)

REM 激活虚拟环境（在批处理中不需要显式激活，但确保使用正确的路径）
call .venv\Scripts\activate.bat

REM 安装uv（如果不存在）
%UV_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装uv包管理器...
    %PIP_CMD% install uv
    if %errorlevel% neq 0 (
        echo 错误：安装uv失败。
        pause
        exit /b 1
    )
)

REM 安装项目依赖
if not exist uv.lock (
    echo 正在安装项目依赖...
    %UV_CMD% pip install -e .
    if %errorlevel% neq 0 (
        echo 错误：安装依赖失败。
        pause
        exit /b 1
    )
) else (
    echo 依赖已安装，跳过安装步骤。
)

REM 创建临时目录
if not exist temp mkdir temp

REM 启动API服务器
cls
 echo DWG to JPG Converter API 服务器已启动
 echo ==================================================
 echo 访问以下地址查看API文档：
 echo http://localhost:8000/docs
 echo http://localhost:8000/redoc
 echo ==================================================
 echo 按 Ctrl+C 停止服务器
 echo ==================================================

%PYTHON_CMD% -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

if %errorlevel% neq 0 (
    echo 错误：服务器启动失败。
    pause
    exit /b 1
)

pause