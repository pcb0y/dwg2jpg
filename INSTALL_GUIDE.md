# 安装和运行指南

本指南将帮助您安装项目依赖并运行DWG到JPG转换API。

## 快速启动

如果是首次运行或遇到依赖错误，请先执行依赖修复：

### 1. 修复依赖问题

- 双击运行 `fix_dependencies.bat` 脚本
- 脚本会：
  - 检查并创建Python虚拟环境（如果不存在）
  - 安装并验证pywin32模块（修复win32com.client导入问题）
  - 安装其他必要依赖
  - 显示安装验证结果

### 2. 启动API服务器

双击运行 `start_server.bat` 脚本，它会自动处理以下任务：

1. 检查并创建Python虚拟环境（如果不存在）
2. 安装uv包管理器
3. 安装项目所有依赖
4. 启动API服务器

该脚本已经设置了UTF-8编码（chcp 65001），可以正确显示中文而不会出现乱码问题。

## 前提条件

- Windows操作系统
- Python 3.9或更高版本
- 已安装AutoCAD软件
- 已安装uv包管理器

## 安装uv包管理器

如果您还没有安装uv，请按照以下步骤安装：

```powershell
# 使用pip安装uv
pip install uv

# 或者从官方源安装（推荐）
winget install astral-sh.uv
```

## 安装项目依赖

在项目根目录下运行以下命令：

```powershell
# 使用uv安装项目依赖
uv pip install -e .

# 或者直接从requirements.txt安装
uv pip install -r requirements.txt
```

## 运行API服务器

有两种方式可以运行API服务器：

### 方式1：直接运行main.py

```powershell
python main.py
```

### 方式2：使用uvicorn运行

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 验证安装

服务器启动后，打开浏览器访问以下地址验证API是否正常运行：

- API根端点：http://localhost:8000/
- API文档：http://localhost:8000/docs
- 备用API文档：http://localhost:8000/redoc

## 常见问题解决

### 问题1：ModuleNotFoundError: No module named 'xxx'

如果运行时出现缺少模块的错误，请确保已正确安装所有依赖：

```powershell
uv pip install -e .
```

### 问题2：AutoCAD相关错误

- 确保您的系统上已安装AutoCAD软件
- 确保您有足够的权限运行AutoCAD COM接口
- 尝试以管理员身份运行API服务器

### 问题3：端口被占用

如果8000端口被占用，可以使用其他端口：

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## 测试转换功能

### 使用项目提供的测试工具

项目提供了两个方便的测试工具：

#### 方法1：使用批处理脚本（推荐）

双击运行 `test_api.bat` 脚本，它会自动使用正确的Python环境运行测试：
- 不带参数：测试API连接是否正常
- 带DWG文件路径参数：测试DWG到JPG转换功能

例如：
```powershell
# 直接双击运行（测试API连接）
test_api.bat

# 或在命令行中指定DWG文件
start test_api.bat "C:\path\to\your\file.dwg"
```

#### 方法2：使用Python脚本

```powershell
# 测试API连接
python test_api.py

# 测试DWG到JPG转换功能
python test_api.py path/to/your/file.dwg
```

#### 方法3：使用curl（高级用户）

```powershell
# 使用curl测试
curl -X POST "http://localhost:8000/convert/dwg-to-jpg" -F "file=@path/to/your/file.dwg" --output converted.jpg
```

## 临时文件清理

转换过程中生成的临时文件存储在`./temp`目录下。如果需要手动清理，可以运行：

```powershell
# 删除所有临时文件
Remove-Item -Path ./temp/* -Recurse -Force
```