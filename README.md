# DWG to JPG Converter API

一个基于FastAPI的RESTful API，用于将DWG文件转换为JPG格式，并支持与数据库集成进行自动化文档管理。

## 功能特点

- 通过HTTP POST请求上传DWG文件并获取转换后的JPG文件
- 支持从数据库读取DWG文件路径并自动转换
- 转换完成后自动将JPG记录插入数据库（C_Attachment表）
- 智能路径处理，支持网络路径、绝对路径和相对路径
- 基于.env文件的灵活配置管理
- 支持异步处理和文件流式传输
- 提供友好的错误处理和日志记录

## 系统要求

- Windows操作系统
- Python 3.9或更高版本
- SQL Server数据库（可选，用于集成功能）
- pip或uv包管理器

## 安装和运行

### 快速启动 (推荐)

1. **修复依赖问题**（如果遇到ModuleNotFoundError错误）：
   - 双击运行 `fix_dependencies.bat` 脚本，它会：
     - 检查并创建虚拟环境
     - 安装并验证pywin32模块（修复win32com.client导入问题）
     - 安装其他必要依赖

2. 配置环境变量：
   - 复制或重命名 `.env.example` 为 `.env`（如果已存在则跳过）
   - 根据您的环境修改 `.env` 文件中的配置项，特别是数据库连接信息和文件路径配置

3. 启动API服务器：
   - 对于简单安装（推荐）：双击运行 `start_simple_server.bat` 脚本
     - 这个脚本使用pip而不是uv来管理依赖，避免了编码问题和win32com安装问题
   - 或者使用原始脚本：双击运行 `start_server.bat` 脚本
   - 脚本会自动：
     - 检查并创建Python虚拟环境（如果不存在）
     - 安装所需的包管理器
     - 安装项目所有依赖
     - 启动API服务器
   - 脚本会处理编码问题并显示友好的启动界面

服务器启动后，可以在浏览器中访问 `http://localhost:8000/docs` 查看API文档和测试接口。

### 手动安装

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
   或使用uv：
   ```bash
   uv pip install -e .
   ```

2. 配置环境变量：
   - 确保 `.env` 文件已正确配置

3. 启动API服务器：
   ```bash
   python main.py
   ```
   或者使用uvicorn直接运行：
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 详细安装说明

请参考 [INSTALL_GUIDE.md](INSTALL_GUIDE.md) 获取详细的安装和配置说明。

## 配置说明

项目使用 `.env` 文件进行配置管理，主要配置项包括：

### 数据库配置
```env
# 数据库连接配置
DB_SERVER=your_server
DB_DATABASE=your_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

### 应用配置
```env
# 应用基础配置
APP_HOST=0.0.0.0
APP_PORT=8000
TEMP_DIR=./temp
```

### 文件路径配置
```env
# 文件路径配置（用于相对路径拼接）
DWG_FILE_PREFIX=D:\Data
```

## API使用方法

### 1. 单文件上传转换

**请求**：
```
POST /convert/dwg-to-jpg
Content-Type: multipart/form-data
```

**表单数据**：
- `file`: 要转换的DWG文件

**示例使用curl**：
```bash
curl -X POST "http://localhost:8000/convert/dwg-to-jpg" -F "file=@path/to/your/file.dwg" --output converted.jpg
```

**示例使用Python requests**：
```python
import requests

url = "http://localhost:8000/convert/dwg-to-jpg"
files = {'file': open('path/to/your/file.dwg', 'rb')}
response = requests.post(url, files=files)

if response.status_code == 200:
    with open('converted.jpg', 'wb') as f:
        f.write(response.content)
    print("转换成功！")
else:
    print(f"转换失败: {response.json()}")
```

### 2. 数据库集成转换

**请求**：
```
POST /convert/database
Content-Type: application/json
```

**请求体**：
```json
{
  "skip_exists_check": false
}
```

**参数说明**：
- `skip_exists_check`: 可选，是否跳过已转换文件的检查（默认false）

**示例使用curl**：
```bash
curl -X POST "http://localhost:8000/convert/database" -H "Content-Type: application/json" -d "{\"skip_exists_check\": false}"
```

## 数据库集成功能

系统支持与SQL Server数据库集成，主要功能包括：

1. **从数据库读取DWG文件信息**：自动查询需要转换的DWG文件
2. **智能路径处理**：自动识别并处理网络路径、绝对路径和相对路径
   - 相对路径会使用 `DWG_FILE_PREFIX` 环境变量进行前缀拼接
3. **JPG记录自动插入**：转换完成后自动将JPG文件信息插入到 `C_Attachment` 表
4. **转换状态标记**：更新原始DWG记录的 `istopdf` 字段表示转换状态（后续版本将更新为 `istojpg`）

### 表结构说明

`C_Attachment` 表包含以下主要字段（用于JPG集成）：
- `Id`: 主键ID
- `RefId`: 关联ID（与原始DWG记录关联）
- `AttachmentType`: 附件类型
- `FileName`: 文件名
- `FilePath`: 文件路径
- `FileSize`: 文件大小
- `CreateBy`: 创建人
- `CreateTime`: 创建时间
- `LastUpdateBy`: 最后更新人
- `LastUpdateTime`: 最后更新时间
- `isdeleted`: 是否删除
- `istopdf`: 转换状态（0=未转换，1=已转换，-1=转换失败）- 后续版本将更新为 `istojpg`

## 依赖检查

运行以下命令检查关键依赖是否正确安装：
```bash
python check_dependencies.py
```

### 直接测试win32com模块
如果只想专门测试win32com相关模块是否正确安装，可以运行：
```bash
python test_win32com.py
```

这个脚本会直接测试win32com.client和pythoncom模块的导入，并提供详细的错误信息和解决方案。

### 解决win32com依赖问题
如果遇到win32com.client模块缺失的问题，请运行专门的英文修复脚本：
```bash
install_basic_deps.bat
```

这个脚本使用英文命令，避免了编码问题，它会：
1. 检查并创建虚拟环境
2. 专门安装pywin32（提供win32com.client模块）
3. 安装所有必要的依赖
4. 验证安装结果

注意：这个脚本使用pip而不是uv来安装pywin32，因为pip更稳定支持这个包。

## 使用测试工具

项目提供了多种测试工具：

### 1. API测试工具

**批处理脚本（推荐）**：

有两个批处理脚本可以用于测试：

```bash
# 简单安装测试（推荐）
test_simple_api.bat

# 原始脚本测试
test_api.bat
```

这两个脚本都可以：
- 不带参数：测试API连接是否正常
- 带DWG文件路径参数：测试DWG到JPG转换功能

例如：
```bash
# 直接双击运行（测试API连接）
test_simple_api.bat

# 或在命令行中指定DWG文件
start test_simple_api.bat "C:\path\to\your\file.dwg"
```

**Python脚本**：

```bash
# 首先确保安装了requests库
pip install requests

# 测试API连接
python test_api.py

# 测试DWG到JPG转换功能
python test_api.py path/to/your/file.dwg
```

### 2. 数据库功能测试

```bash
# 测试数据库连接
test_db_connection.py

# 测试数据库查询
test_database_query.py

# 测试JPG插入数据库功能
test_updated_insert_jpg.py
```

### 3. 路径处理测试

```bash
# 测试路径前缀拼接逻辑
python test_path_prefix.py
```

## 注意事项

- 转换过程中AutoCAD会在后台启动，但不会显示界面
- 大文件转换可能需要较长时间
- 请确保您的系统上安装了AutoCAD软件
- API会自动清理临时文件，但在异常情况下可能需要手动清理`./temp`目录
- 使用数据库集成功能时，请确保`.env`文件中的数据库连接信息正确
- 路径处理逻辑会自动识别网络路径（以\\开头）、绝对路径（包含:）和相对路径
- 转换状态通过`istopdf`字段标识：0=未转换，1=已转换，-1=转换失败（后续版本将更新为 `istojpg`）

## 许可证

[MIT](LICENSE)