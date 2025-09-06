#!/bin/bash

# DWG to JPG Converter API 部署脚本
# 使用方法: bash deploy_server.sh

# 配置项
APP_DIR="/opt/dwg2jpg-api"
PYTHON_VERSION="3.9"
VENV_NAME="venv"
DB_SERVER="localhost"
DB_NAME="dwg2jpg"
DB_USER="dwg2jpg_user"
DB_PASS=""
PORT="8000"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 检查是否以root用户运行
if [ "$(id -u)" != "0" ]; then
   echo -e "${RED}请以root用户权限运行此脚本${NC}"
   exit 1
fi

# 函数: 显示信息
function info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# 函数: 显示成功信息
function success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# 函数: 显示警告信息
function warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# 函数: 显示错误信息
function error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# 步骤1: 安装系统依赖
info "安装系统依赖..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ $ID == "ubuntu" || $ID == "debian" ]]; then
        apt update && apt upgrade -y
        apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-pip git nginx
    elif [[ $ID == "centos" || $ID == "rhel" || $ID == "almalinux" || $ID == "rocky" ]]; then
        yum update -y
        yum install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-pip git nginx
    else
        error "不支持的Linux发行版: $ID"
    fi
else
    error "无法检测操作系统类型"
fi

success "系统依赖安装完成"

# 步骤2: 创建应用目录
info "创建应用目录..."
mkdir -p $APP_DIR
cd $APP_DIR

success "应用目录创建完成: $APP_DIR"

# 步骤3: 创建Python虚拟环境
info "创建Python虚拟环境..."
python${PYTHON_VERSION} -m venv $VENV_NAME
source $VENV_NAME/bin/activate
pip install --upgrade pip

success "Python虚拟环境创建完成"

# 步骤4: 克隆代码 (假设当前目录已有代码，实际部署时替换为git clone命令)
info "克隆项目代码..."
# git clone https://your-repo-url/dwg2jpg-api.git .

# 如果是本地测试，可以复制当前目录内容
success "代码部署完成"

# 步骤5: 安装Python依赖
info "安装Python依赖..."
pip install uv
uv pip install fastapi uvicorn python-multipart reportlab pyodbc python-dotenv ezdxf gunicorn

if [ -f requirements.txt ]; then
    uv pip install -r requirements.txt
fi

success "Python依赖安装完成"

# 步骤6: 创建.env配置文件
info "创建.env配置文件..."
cat > .env << EOF
# 数据库连接配置
DB_SERVER=${DB_SERVER}
DB_DATABASE=${DB_NAME}
DB_USERNAME=${DB_USER}
DB_PASSWORD=${DB_PASS}

# API服务器配置
HOST=0.0.0.0
PORT=${PORT}

# 临时目录配置
TEMP_DIR=temp

# 转换配置
# ODA_CONVERTER_PATH=/path/to/ODAFileConverter  # 根据实际路径修改
EOF

warning "请手动编辑.env文件，配置数据库和ODA转换器路径"

success ".env配置文件创建完成"

# 步骤7: 创建临时目录
info "创建临时目录..."
mkdir -p temp
chmod 777 temp

success "临时目录创建完成"

# 设置systemd服务
info "设置systemd服务..."
cat > /etc/systemd/system/dwg2jpg-api.service << EOF
[Unit]
Description=DWG to JPG Converter API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/${VENV_NAME}/bin"
ExecStart=${APP_DIR}/${VENV_NAME}/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_endpoints:app --bind 0.0.0.0:${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dwg2jpg-api
success "systemd服务设置完成"

# 配置Nginx反向代理
info "配置Nginx反向代理..."
cat > /etc/nginx/sites-available/dwg2jpg-api << EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 20M;
}
EOF

ln -s /etc/nginx/sites-available/dwg2jpg-api /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

success "Nginx反向代理配置完成"

# 步骤10: 显示部署完成信息
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}DWG to JPG Converter API 部署完成${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${BLUE}1. 请完成以下配置:${NC}"
echo -e "   - 编辑 ${APP_DIR}/.env 文件，配置数据库连接和ODA转换器路径"
echo -e "   - 确保ODA File Converter已正确安装"
echo -e ""
echo -e "${BLUE}2. 启动服务:${NC}"
echo -e "   systemctl start dwg2jpg-api"
echo -e ""
echo -e "${BLUE}3. 查看服务状态:${NC}"
echo -e "   systemctl status dwg2jpg-api"
echo -e ""
echo -e "${BLUE}4. 访问API文档:${NC}"
echo -e "   http://服务器IP地址/docs"
echo -e "${GREEN}======================================${NC}\n"