# DWG to PDF Converter API 服务器部署指南

本指南将帮助您在生产服务器上部署DWG to PDF Converter API应用。

## 目录

- [1. 服务器环境准备](#1-服务器环境准备)
- [2. Python环境设置](#2-python环境设置)
- [3. 代码部署](#3-代码部署)
- [4. 依赖安装](#4-依赖安装)
- [5. 配置文件设置](#5-配置文件设置)
- [6. ODA文件转换器安装](#6-oda文件转换器安装)
- [7. 服务启动配置](#7-服务启动配置)
  - [7.1 使用Gunicorn和Uvicorn Workers](#71-使用gunicorn和-uvicorn-workers)
  - [7.2 使用systemd管理服务](#72-使用systemd管理服务)
- [8. 反向代理设置(Nginx)](#8-反向代理设置nginx)
- [9. 自动化部署脚本](#9-自动化部署脚本)
- [10. 监控与日志](#10-监控与日志)
- [11. 常见问题排查](#11-常见问题排查)

## 1. 服务器环境准备

### 硬件要求
- CPU: 2核或以上
- 内存: 4GB或以上
- 磁盘空间: 至少20GB可用空间

### 操作系统要求
- Ubuntu 20.04/22.04 或其他Linux发行版
- Windows Server 2019/2022

本指南主要针对Linux环境，Windows环境部署在相应部分会有特别说明。

### 必要软件安装

**Ubuntu/Debian:**
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx
```

**CentOS/RHEL:**
```bash
yum update -y
yum install -y python3 python3-pip git nginx
dnf module enable python39 -y  # 如需安装特定Python版本
```

## 2. Python环境设置

### 创建虚拟环境
```bash
# 选择一个目录作为应用根目录
mkdir -p /opt/dwg2pdf-api
cd /opt/dwg2pdf-api

# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 更新pip到最新版本
pip install --upgrade pip
```

## 3. 代码部署

使用git克隆项目代码（或上传打包好的代码）：

```bash
# 克隆代码（假设您有git访问权限）
git clone https://your-repo-url/dwg2pdf-api.git .

# 或者上传代码包并解压
tar -xzf dwg2pdf-api.tar.gz -C .
```

## 4. 依赖安装

### 使用uv安装依赖

```bash
# 安装uv包管理器
pip install uv

# 使用uv安装项目依赖
uv pip install fastapi uvicorn python-multipart reportlab pyodbc python-dotenv ezdxf gunicorn

# 如果有requirements.txt文件
if [ -f requirements.txt ]; then
    uv pip install -r requirements.txt
fi
```

## 5. 配置文件设置

### 创建.env配置文件

复制.env.example并根据您的环境修改配置：

```bash
cp .env.example .env
nano .env  # 或使用您喜欢的编辑器
```

**关键配置项说明：**

```ini
# 数据库连接配置
DB_SERVER=your_db_server_address
DB_DATABASE=your_database_name
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password

# API服务器配置
HOST=0.0.0.0
PORT=8000

# 临时目录配置
TEMP_DIR=temp

# 转换配置
ODA_CONVERTER_PATH=/path/to/ODAFileConverter.exe  # Windows环境
# ODA_CONVERTER_PATH=/path/to/ODAFileConverter      # Linux环境
```

## 6. ODA文件转换器安装

这个应用依赖ODA File Converter进行DWG文件转换，需要确保它已正确安装。

### Windows环境

1. 从ODA官网下载ODA File Converter
2. 安装到指定目录（如`C:\ODA\ODAFileConverter26.7.0`）
3. 在.env文件中设置正确的路径

### Linux环境

1. 从ODA官网下载Linux版本的ODA File Converter
2. 解压到指定目录（如`/opt/ODA/ODAFileConverter26.7.0`）
3. 确保有执行权限：`chmod +x /opt/ODA/ODAFileConverter26.7.0/ODAFileConverter`
4. 在.env文件中设置正确的路径

## 7. 服务启动配置

### 7.1 使用Gunicorn和Uvicorn Workers

在生产环境中，建议使用Gunicorn作为WSGI服务器，配合Uvicorn workers：

```bash
# 安装Gunicorn
pip install gunicorn uvicorn

# 启动服务（测试）
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_endpoints:app --bind 0.0.0.0:8000
```

### 7.2 使用systemd管理服务

创建systemd服务文件以确保应用在系统启动时自动运行，并在崩溃时自动重启：

```bash
nano /etc/systemd/system/dwg2pdf-api.service
```

添加以下内容（根据您的实际路径修改）：

```ini
[Unit]
Description=DWG to PDF Converter API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/dwg2pdf-api
Environment="PATH=/opt/dwg2pdf-api/venv/bin"
ExecStart=/opt/dwg2pdf-api/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_endpoints:app --bind 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
systemctl daemon-reload
systemctl enable dwg2pdf-api
systemctl start dwg2pdf-api

# 检查服务状态
systemctl status dwg2pdf-api
```

## 8. 反向代理设置(Nginx)

为了提供更好的性能和安全性，建议使用Nginx作为反向代理：

```bash
nano /etc/nginx/sites-available/dwg2pdf-api
```

添加以下配置（替换your_domain.com为您的域名）：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件配置（如果有）
    location /static/ {
        alias /opt/dwg2pdf-api/static/;
        expires 30d;
    }

    # 增加上传文件大小限制
    client_max_body_size 20M;
}
```

启用配置并重启Nginx：

```bash
ln -s /etc/nginx/sites-available/dwg2pdf-api /etc/nginx/sites-enabled/
nginx -t  # 检查配置是否正确
systemctl restart nginx
```

## 9. 自动化部署脚本

为了简化部署过程，您可以创建一个自动化部署脚本：

```bash
nano deploy.sh
chmod +x deploy.sh
```

脚本内容示例：

```bash
#!/bin/bash

# 部署目录
APP_DIR="/opt/dwg2pdf-api"
VENV_DIR="$APP_DIR/venv"

# 停止服务
systemctl stop dwg2pdf-api

# 进入应用目录
cd $APP_DIR

# 拉取最新代码
git pull origin main

# 激活虚拟环境
source $VENV_DIR/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 重启服务
systemctl start dwg2pdf-api

# 查看服务状态
systemctl status dwg2pdf-api
```

## 10. 监控与日志

### 查看应用日志

```bash
# 使用journalctl查看服务日志
journalctl -u dwg2pdf-api -f

# 或者查看FastAPI的日志文件（如果配置了日志记录到文件）
# 根据logger_config.py中的配置查看相应日志文件
```

### Nginx日志

```bash
# 访问日志
cat /var/log/nginx/access.log

# 错误日志
cat /var/log/nginx/error.log
```

## 11. 常见问题排查

### 数据库连接问题
- 确认数据库服务器允许远程连接
- 检查防火墙设置是否允许访问数据库端口
- 验证.env文件中的数据库凭证是否正确

### ODA文件转换器问题
- 确认ODA转换器路径设置正确
- 检查ODA转换器是否有执行权限
- 验证ODA转换器版本与应用兼容

### 内存或性能问题
- 调整Gunicorn的worker数量（-w参数）
- 考虑增加服务器内存或CPU资源
- 监控系统资源使用情况：`htop`或`top`

### API请求超时
- 检查Nginx和Gunicorn的超时设置
- 对于大型DWG文件，可能需要增加超时时间

---

部署完成后，您可以通过浏览器访问 `http://your_domain.com/docs` 查看API文档和测试接口。