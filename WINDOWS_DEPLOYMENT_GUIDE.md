# DWG to JPG Converter API Windows服务器部署指南

本指南将帮助您在Windows Server环境下部署DWG to JPG Converter API应用。

## 目录

- [1. 服务器环境准备](#1-服务器环境准备)
- [2. Python环境安装](#2-python环境安装)
- [3. 代码部署](#3-代码部署)
- [4. 依赖安装](#4-依赖安装)
- [5. 配置文件设置](#5-配置文件设置)
- [6. ODA文件转换器安装](#6-oda文件转换器安装)
- [7. 服务配置](#7-服务配置)
  - [7.1 使用Windows服务](#71-使用windows服务)
  - [7.2 使用IIS作为反向代理](#72-使用iis作为反向代理)
- [8. 自动化部署脚本](#8-自动化部署脚本)
- [9. 监控与日志](#9-监控与日志)
- [10. 常见问题排查](#10-常见问题排查)

## 1. 服务器环境准备

### 硬件要求
- CPU: 2核或以上
- 内存: 4GB或以上
- 磁盘空间: 至少20GB可用空间

### 操作系统要求
- Windows Server 2016/2019/2022
- Windows 10/11专业版（适用于测试环境）

### 必要软件安装

1. **Microsoft Visual C++ Redistributable**
   - 从微软官网下载并安装最新版本的Visual C++ Redistributable

2. **IIS (Internet Information Services)**
   - 打开"服务器管理器" > "添加角色和功能"
   - 勾选"Web服务器(IIS)"并完成安装
   - 安装完成后，确保启用以下角色服务：
     - Web服务器 > 应用程序开发 > CGI
     - Web服务器 > 应用程序开发 > ISAPI扩展
     - Web服务器 > 应用程序开发 > ISAPI筛选器

3. **URL重写模块**
   - 从微软官网下载并安装[IIS URL重写模块](https://www.iis.net/downloads/microsoft/url-rewrite)

4. **ARR (Application Request Routing)**
   - 从微软官网下载并安装[IIS ARR模块](https://www.iis.net/downloads/microsoft/application-request-routing)

## 2. Python环境安装

1. **下载并安装Python**
   - 访问[Python官方网站](https://www.python.org/downloads/)
   - 下载Python 3.9或更高版本的Windows安装包
   - 运行安装程序，勾选"Add Python to PATH"选项
   - 选择"Customize installation"，确保安装pip

2. **验证Python安装**
   - 打开命令提示符(cmd)
   - 运行以下命令验证安装：
     ```cmd
     python --version
     pip --version
     ```

## 3. 代码部署

1. **创建应用目录**
   ```cmd
   mkdir C:\dwg2jpg-api
   cd C:\dwg2jpg-api
   ```

2. **获取项目代码**
   - 使用Git克隆代码（推荐）：
     ```cmd
     git clone https://your-repo-url/dwg2jpg-api.git .
     ```
   - 或者直接复制项目文件到`C:\dwg2jpg-api`目录

## 4. 依赖安装

1. **创建虚拟环境**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

2. **安装uv包管理器**
   ```cmd
   pip install uv
   ```

3. **安装项目依赖**
   ```cmd
   uv pip install fastapi uvicorn python-multipart reportlab pyodbc python-dotenv ezdxf gunicorn
   
   # 如果有requirements.txt文件
   if exist requirements.txt (
       uv pip install -r requirements.txt
   )
   ```

## 5. 配置文件设置

1. **创建.env配置文件**
   - 复制`.env.example`文件并重命名为`.env`
   - 使用记事本或其他文本编辑器打开`.env`文件
   - 根据您的环境修改配置项：

     ```ini
     # 数据库连接配置
     DB_SERVER=localhost
     DB_DATABASE=your_database
     DB_USERNAME=your_username
     DB_PASSWORD=your_password
     
     # API服务器配置
     HOST=127.0.0.1
     PORT=8000
     
     # 临时目录配置
     TEMP_DIR=temp
     
     # ODA转换器路径
     ODA_CONVERTER_PATH=C:\ODA\ODAFileConverter26.7.0\ODAFileConverter.exe
     ```

## 6. ODA文件转换器安装

1. **下载ODA File Converter**
   - 从[ODA官网](https://www.opendesign.com/guestfiles/oda_file_converter)
   下载Windows版本的ODA File Converter

2. **安装ODA File Converter**
   - 运行安装程序，按照向导完成安装
   - 建议安装到`C:\ODA\ODAFileConverter26.7.0`目录

3. **配置环境变量**
   - 确保在`.env`文件中正确设置了`ODA_CONVERTER_PATH`指向安装路径

## 7. 服务配置

### 7.1 使用Windows服务

推荐使用[WinSW](https://github.com/winsw/winsw)将应用注册为Windows服务。

1. **下载WinSW**
   - 从[WinSW GitHub发布页](https://github.com/winsw/winsw/releases)下载最新版本的WinSW
   - 将下载的文件重命名为`dwg2jpg-api-service.exe`并复制到`C:\dwg2jpg-api`目录

2. **创建服务配置文件**
   - 在`C:\dwg2jpg-api`目录创建`dwg2jpg-api-service.xml`文件
   - 添加以下内容（根据您的实际路径修改）：

     ```xml
     <service>
       <id>dwg2jpg-api</id>
       <name>DWG to JPG Converter API</name>
       <description>提供DWG文件转换为JPG的Web服务</description>
       <executable>C:\dwg2jpg-api\venv\Scripts\python.exe</executable>
       <arguments>-m uvicorn api_endpoints:app --host 127.0.0.1 --port 8000</arguments>
       <workingdirectory>C:\dwg2jpg-api</workingdirectory>
       <logpath>C:\dwg2jpg-api\logs</logpath>
       <logmode>rotate</logmode>
       <onfailure action="restart" delay="10 sec"/>
       <onfailure action="restart" delay="20 sec"/>
       <onfailure action="restart" delay="30 sec"/>
       <env name="PYTHONIOENCODING" value="utf-8" />
     </service>
     ```

3. **创建日志目录**
   ```cmd
   mkdir C:\dwg2jpg-api\logs
   ```

4. **安装并启动服务**
   ```cmd
   cd C:\dwg2jpg-api
   dwg2jpg-api-service.exe install
   dwg2jpg-api-service.exe start
   ```

5. **管理服务**
   ```cmd
   # 停止服务
   dwg2jpg-api-service.exe stop
   
   # 卸载服务
   dwg2jpg-api-service.exe uninstall
   
   # 查看服务状态
   sc query dwg2jpg-api
   ```

### 7.2 使用IIS作为反向代理

1. **打开IIS管理器**
   - 点击开始菜单 > 管理工具 > Internet Information Services (IIS) 管理器

2. **创建新网站**
   - 在左侧面板右击"网站" > "添加网站"
   - 设置网站名称（如"DWG2JPG-API"）
   - 设置物理路径（如"C:\dwg2jpg-api"）
   - 设置绑定：
     - 类型：HTTP
     - IP地址：全部未分配
     - 端口：80（或您希望使用的端口）
   - 点击"确定"创建网站

3. **配置URL重写规则**
   - 选择创建的网站
   - 双击"URL重写"图标
   - 点击右侧"添加规则" > "空白规则" > "确定"
   - 设置以下内容：
     - 名称：ReverseProxyInboundRule1
     - 匹配URL：
       - 请求的URL：与模式匹配
       - 使用：正则表达式
       - 模式：(.*)
     - 条件：无需添加
     - 操作：
       - 操作类型：重写
       - 重写URL：http://127.0.0.1:8000/{R:1}
   - 点击"应用"保存配置

4. **配置ARR**
   - 在左侧面板选择服务器名称
   - 双击"Application Request Routing Cache"
   - 点击右侧"Server Proxy Settings"
   - 勾选"启用代理"，然后点击"应用"

5. **重启IIS**
   ```cmd
   iisreset
   ```

## 8. 自动化部署脚本

创建一个批处理脚本以简化部署过程：

1. **创建`deploy_windows.bat`文件**
   ```cmd
   @echo off
   
   echo ===================================================
echo DWG to JPG Converter API Windows部署脚本
echo ===================================================

:: 配置项
set APP_DIR=C:\dwg2jpg-api
   set VENV_NAME=venv
   set PORT=8000
   
   :: 步骤1: 创建应用目录
   echo 1. 创建应用目录...
   mkdir %APP_DIR% 2>nul
   cd %APP_DIR%
   
   :: 步骤2: 创建虚拟环境
   echo 2. 创建Python虚拟环境...
   python -m venv %VENV_NAME%
   call %VENV_NAME%\Scripts\activate.bat
   pip install --upgrade pip
   
   :: 步骤3: 安装依赖
   echo 3. 安装项目依赖...
   pip install uv
   uv pip install fastapi uvicorn python-multipart reportlab pyodbc python-dotenv ezdxf
   
   if exist requirements.txt (
       uv pip install -r requirements.txt
   )
   
   :: 步骤4: 创建临时目录
   echo 4. 创建临时目录...
   mkdir temp 2>nul
   
   :: 步骤5: 显示完成信息
   echo ===================================================
   echo 部署完成！请手动完成以下配置：
   echo 1. 复制.env.example并重命名为.env，配置数据库连接
   echo 2. 安装并配置ODA File Converter
   echo 3. 使用WinSW配置Windows服务
   echo 4. 配置IIS反向代理（可选）
   echo ===================================================
   
   pause
   ```

2. **运行脚本**
   - 以管理员身份运行命令提示符
   - 执行脚本：
     ```cmd
     cd C:\path\to\script
     deploy_windows.bat
     ```

## 9. 监控与日志

### 应用日志
- WinSW服务日志：`C:\dwg2jpg-api\logs`目录
- 根据`logger_config.py`中的配置查看应用日志

### IIS日志
- 默认位于`C:\inetpub\logs\LogFiles`目录
- 可在IIS管理器中配置日志路径和格式

## 10. 常见问题排查

### 数据库连接问题
- 确认SQL Server允许远程连接
- 检查防火墙设置是否允许访问数据库端口（默认为1433）
- 验证`.env`文件中的数据库凭证是否正确
- 确保已安装pyodbc依赖：`pip install pyodbc`

### ODA文件转换器问题
- 确认ODA转换器路径设置正确
- 检查ODA转换器是否有管理员权限运行
- 验证ODA转换器版本与应用兼容

### 服务启动失败
- 检查WinSW日志获取详细错误信息
- 验证Python路径和参数设置正确
- 确保所有依赖已正确安装

### IIS反向代理问题
- 确认URL重写规则配置正确
- 验证ARR已启用代理功能
- 检查IIS日志获取详细错误信息

---

部署完成后，您可以通过浏览器访问 `http://服务器IP地址/docs` 查看API文档和测试接口。