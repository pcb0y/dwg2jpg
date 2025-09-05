@echo off
REM 专门解决win32com依赖问题的安装脚本
REM 使用pip而不是uv来安装，因为pip更稳定支持pywin32

cls
echo ==================================================
echo 正在安装DWG to PDF Converter API所需依赖
特别处理win32com依赖问题
==================================================

echo. 

echo 1. 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python。请先安装Python 3.9或更高版本。
    pause
    exit /b 1
)

echo. 
echo 2. 检查并创建虚拟环境...
if not exist .venv (
    echo 创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo 错误：创建虚拟环境失败。
        pause
        exit /b 1
    )
) else (
    echo 虚拟环境已存在
)

echo. 
echo 3. 激活虚拟环境...
call .venv\Scripts\activate.bat

if %errorlevel% neq 0 (
    echo 错误：激活虚拟环境失败。
    pause
    exit /b 1
)

echo. 
echo 4. 升级pip...
python -m pip install --upgrade pip

if %errorlevel% neq 0 (
    echo 警告：pip升级失败，但继续尝试安装依赖。
)

echo. 
echo 5. 安装pywin32（这将提供win32com.client模块）...
pip install pywin32==305

if %errorlevel% neq 0 (
    echo 错误：pywin32安装失败！
    echo 请尝试手动安装：
    echo 1. 打开命令提示符
    echo 2. 执行：.venv\Scripts\activate.bat
    echo 3. 执行：pip install pywin32
    pause
    exit /b 1
)

echo. 
echo 6. 安装其他依赖...
pip install fastapi uvicorn python-multipart pyautocad reportlab

if %errorlevel% neq 0 (
    echo 警告：部分依赖安装可能失败，但继续验证关键组件。
)

echo. 
echo 7. 验证win32com依赖安装...
python -c "import win32com.client; import pythoncom; print('✅ win32com.client 和 pythoncom 导入成功！')"

if %errorlevel% neq 0 (
    echo 错误：win32com.client 导入失败！
    echo 尝试以下解决方案：
    echo 1. 确认您使用的是32位Python还是64位Python，确保与AutoCAD版本匹配
    echo 2. 重新安装pywin32：pip uninstall pywin32 && pip install pywin32
    echo 3. 检查是否有多个Python版本冲突
    pause
    exit /b 1
)

echo. 
echo 8. 验证其他关键依赖...
python -c "import fastapi; import uvicorn; print('✅ FastAPI 和 Uvicorn 导入成功！')"

if %errorlevel% neq 0 (
    echo 警告：部分Web依赖导入失败，但win32com已成功安装。
)

echo.
echo ==================================================
echo 安装完成！
echo ✅ win32com依赖问题已解决。
echo 现在可以运行 start_server.bat 启动API服务器了。
echo 如果仍然遇到问题，请检查您的Python版本与AutoCAD版本是否兼容。
echo ==================================================

pause