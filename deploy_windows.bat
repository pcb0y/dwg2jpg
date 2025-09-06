@echo off

REM 设置控制台编码为UTF-8
chcp 65001 >nul

cls
echo ===================================================
echo DWG to PDF Converter API Windows部署脚本

echo 此脚本将帮助您在Windows服务器上部署DWG转PDF转换服务
echo 请确保以管理员身份运行此脚本

echo ===================================================

REM 配置项 - 用户可根据需要修改
echo 正在设置配置项...
set "APP_DIR=C:\dwg2pdf-api"
set "VENV_NAME=venv"
set "PORT=8000"

REM 检查Python是否已安装
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python。请先安装Python并添加到PATH环境变量。
    echo 推荐安装Python 3.9或更高版本。
    pause
    exit /b 1
)

REM 步骤1: 创建应用目录
echo.
echo ===================================================
echo 步骤1: 创建应用目录
mkdir "%APP_DIR%" 2>nul
if %ERRORLEVEL% neq 0 (
    echo 警告: 应用目录已存在。继续使用现有目录。
) else (
    echo 应用目录已创建: %APP_DIR%
)
cd /d "%APP_DIR%" || (
    echo 错误: 无法进入应用目录。请检查权限。
    pause
    exit /b 1
)

REM 步骤2: 创建Python虚拟环境
echo.
echo ===================================================
echo 步骤2: 创建Python虚拟环境
if not exist "%VENV_NAME%" (
    echo 创建虚拟环境: %VENV_NAME%
    python -m venv "%VENV_NAME%"
    if %ERRORLEVEL% neq 0 (
        echo 错误: 创建虚拟环境失败。
        pause
        exit /b 1
    )
) else (
    echo 警告: 虚拟环境已存在。跳过创建步骤。
)

REM 激活虚拟环境
echo 激活虚拟环境...
call "%VENV_NAME%\Scripts\activate.bat"
if %ERRORLEVEL% neq 0 (
    echo 错误: 激活虚拟环境失败。
    pause
    exit /b 1
)

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip >nul 2>&1

REM 步骤3: 安装项目依赖
echo.
echo ===================================================
echo 步骤3: 安装项目依赖

REM 安装uv包管理器
echo 安装uv包管理器...
pip install uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 警告: 安装uv失败，将使用pip安装依赖。
)

REM 安装核心依赖
echo 安装核心依赖包...
if exist "%APP_DIR%\requirements.txt" (
    echo 发现requirements.txt文件，使用其中的依赖列表
    if command /v:on >nul 2>&1 && (uv --version >nul 2>&1) (
        uv pip install -r "%APP_DIR%\requirements.txt" >nul 2>&1
    ) else (
        pip install -r "%APP_DIR%\requirements.txt" >nul 2>&1
    )
) else (
    echo 未发现requirements.txt文件，安装必要的核心依赖
    set "CORE_DEPS=fastapi uvicorn python-multipart reportlab pyodbc python-dotenv ezdxf"
    if command /v:on >nul 2>&1 && (uv --version >nul 2>&1) (
        uv pip install %CORE_DEPS% >nul 2>&1
    ) else (
        pip install %CORE_DEPS% >nul 2>&1
    )
)

if %ERRORLEVEL% neq 0 (
    echo 错误: 安装依赖失败。请检查网络连接。
    pause
    exit /b 1
)

REM 步骤4: 创建配置文件
echo.
echo ===================================================
echo 步骤4: 创建配置文件
if not exist "%APP_DIR%\.env" (
    if exist "%APP_DIR%\.env.example" (
        echo 复制.env.example到.env
        copy "%APP_DIR%\.env.example" "%APP_DIR%\.env" >nul
    ) else (
        echo 创建默认.env文件
        (echo # 数据库连接配置
        echo DB_SERVER=localhost
        echo DB_DATABASE=your_database
        echo DB_USERNAME=your_username
        echo DB_PASSWORD=your_password
        echo.
        echo # API服务器配置
        echo HOST=127.0.0.1
        echo PORT=%PORT%
        echo.
        echo # 临时目录配置
        echo TEMP_DIR=temp
        echo.
        echo # ODA转换器路径
        echo ODA_CONVERTER_PATH=C:\ODA\ODAFileConverter26.7.0\ODAFileConverter.exe) > "%APP_DIR%\.env"
    )
    echo 配置文件已创建: %APP_DIR%\.env
    echo 警告: 请务必编辑.env文件配置数据库连接信息和ODA转换器路径！
) else (
    echo 警告: .env文件已存在。跳过创建步骤。
)

REM 步骤5: 创建临时目录
echo.
echo ===================================================
echo 步骤5: 创建临时目录
mkdir "%APP_DIR%\temp" 2>nul
if %ERRORLEVEL% neq 0 (
    echo 警告: 临时目录已存在。跳过创建步骤。
) else (
    echo 临时目录已创建: %APP_DIR%\temp
)

REM 步骤6: 安装Windows服务配置
echo.
echo ===================================================
echo 步骤6: 配置Windows服务
set "WINSW_EXE=%APP_DIR%\dwg2pdf-api-service.exe"
set "WINSW_XML=%APP_DIR%\dwg2pdf-api-service.xml"

if not exist "%WINSW_EXE%" (
    echo 警告: 未找到WinSW可执行文件。请手动下载并配置Windows服务。
    echo 下载地址: https://github.com/winsw/winsw/releases
    echo 重命名为: dwg2pdf-api-service.exe
) else (
    echo 创建Windows服务配置文件...
    (echo ^<service^>
    echo   ^<id^>dwg2pdf-api^</id^>
    echo   ^<name^>DWG to PDF Converter API^</name^>
    echo   ^<description^>提供DWG文件转换为PDF/JPG的Web服务^</description^>
    echo   ^<executable^>%APP_DIR%\%VENV_NAME%\Scripts\python.exe^</executable^>
    echo   ^<arguments^>-m uvicorn api_endpoints:app --host 127.0.0.1 --port %PORT%^</arguments^>
    echo   ^<workingdirectory^>%APP_DIR%^</workingdirectory^>
    echo   ^<logpath^>%APP_DIR%\logs^</logpath^>
    echo   ^<logmode^>rotate^</logmode^>
    echo   ^<onfailure action="restart" delay="10 sec"/^
    echo   ^<onfailure action="restart" delay="20 sec"/^
    echo   ^<onfailure action="restart" delay="30 sec"/^
    echo   ^<env name="PYTHONIOENCODING" value="utf-8" /^
    echo ^</service^>) > "%WINSW_XML%"
    echo Windows服务配置文件已创建: %WINSW_XML%
    
    REM 创建日志目录
    mkdir "%APP_DIR%\logs" 2>nul
    echo 日志目录已创建: %APP_DIR%\logs
)

REM 步骤7: 显示完成信息
echo.
echo ===================================================
echo 部署脚本执行完成！
echo ===================================================
echo.
echo 以下为您需要手动完成的配置步骤：
echo.
echo 1. 编辑配置文件
   路径: %APP_DIR%\.env
   请设置正确的数据库连接信息和ODA转换器路径

echo 2. 安装ODA File Converter
   下载地址: https://www.opendesign.com/guestfiles/oda_file_converter
   建议安装到: C:\ODA\ODAFileConverter26.7.0

echo 3. 注册Windows服务
   以管理员身份打开命令提示符，执行:
   cd %APP_DIR%
   dwg2pdf-api-service.exe install
   dwg2pdf-api-service.exe start

echo 4. 可选：配置IIS作为反向代理
   请参考WINDOWS_DEPLOYMENT_GUIDE.md中的详细说明

echo 5. 验证服务
   浏览器访问: http://localhost:%PORT%/docs

echo.
echo 如果需要卸载服务，请执行:
   dwg2pdf-api-service.exe uninstall

echo ===================================================
echo 如有问题，请参考WINDOWS_DEPLOYMENT_GUIDE.md文档

pause