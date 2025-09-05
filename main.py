import os
import tempfile
from pathlib import Path
import logging
import pyodbc
from dotenv import load_dotenv
import datetime
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
# 导入我们新创建的转换包
from dwg2pdf_converter import convert_dwg_to_pdf as converter_dwg_to_pdf
# 加载.env文件中的环境变量
load_dotenv()

# 配置日志
# 创建logger对象
logger = logging.getLogger("dwg2pdf-api")
logger.setLevel(logging.INFO)

# 创建日志目录
log_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建控制台处理器并设置级别为INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 创建文件处理器并设置级别为INFO
# 使用日期命名日志文件，便于管理
log_file = os.path.join(log_dir, f"dwg2pdf_api_{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# 为logger添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class SQLDatabase:
    """SQL Server数据库连接类，从环境变量读取配置"""
    
    def __init__(self):
        # 从环境变量中读取数据库连接配置
        self.server = os.getenv("DB_SERVER", "localhost")  # 服务器地址
        self.database = os.getenv("DB_DATABASE", "DWG2PDF")  # 数据库名称
        self.username = os.getenv("DB_USERNAME", "sa")  # 用户名
        self.password = os.getenv("DB_PASSWORD", "your_password")  # 密码
        self.driver = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")  # ODBC驱动
        self.conn = None
    
    def connect(self):
        """连接到SQL Server数据库"""
        try:
            # 创建连接字符串
            conn_str = f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}"
            
            # 建立连接
            self.conn = pyodbc.connect(conn_str)
            logger.info(f"成功连接到数据库: {self.server}/{self.database}")
            return self.conn
        except pyodbc.Error as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("数据库连接已关闭")
    
    def execute_query(self, query, params=None):
        """执行SQL查询并返回结果"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 如果是SELECT语句，返回结果
            if query.strip().upper().startswith("SELECT"):
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                # 对于其他语句，提交并返回受影响的行数
                self.conn.commit()
                return cursor.rowcount
        except pyodbc.Error as e:
            logger.error(f"SQL查询执行失败: {str(e)}")
            self.conn.rollback()
            raise
        finally:
            cursor.close()
    
    def select_query(self, query, params=None):
        """用于select操作的包装方法，确保与现有代码兼容"""
        return self.execute_query(query, params)
    
    def get_connection(self):
        """获取数据库连接对象"""
        if not self.conn:
            self.connect()
        return self.conn


# 创建数据库实例
db = SQLDatabase()

# 在应用启动时初始化数据库
def init_database():
    """初始化数据库，创建必要的表"""
    try:
        # 创建转换历史表
        create_table_query = """
            IF NOT EXISTS (
                SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id 
                WHERE t.name = 'conversion_history' AND s.name = 'dbo'
            )
            BEGIN
                CREATE TABLE conversion_history (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    file_name NVARCHAR(255) NOT NULL,
                    original_path NVARCHAR(1000) NOT NULL,
                    pdf_path NVARCHAR(1000) NOT NULL,
                    conversion_time DATETIME DEFAULT GETDATE(),
                    status NVARCHAR(50) NOT NULL,
                    file_size BIGINT,
                    error_message NVARCHAR(MAX)
                )
                PRINT 'conversion_history 表已创建'
            END
            ELSE
            BEGIN
                PRINT 'conversion_history 表已存在'
            END
        """
        db.execute_query(create_table_query)
        logger.info("数据库表初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        # 不阻止应用启动，但记录错误


# 创建FastAPI应用
app = FastAPI(title="DWG到PDF转换器API", description="用于将DWG文件转换为PDF格式的API")

# 在应用启动事件中初始化数据库
@app.on_event("startup")
async def startup_event():
    init_database()
    
    # 启动定期检查和转换任务
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_check_and_convert())

# 定期检查并转换数据库中的DWG文件
async def periodic_check_and_convert():
    """定期从数据库查询需要转换的DWG文件并进行转换"""
    import asyncio
    import time
    
    # 从环境变量获取检查间隔，默认为60秒
    check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
    
    logger.info(f"开始定期检查数据库中的DWG文件，检查间隔: {check_interval}秒")
    
    while True:
        try:
            # 执行查询获取需要转换的DWG文件
            dwg_files = get_dwg_files_from_database()
            
            if dwg_files:
                logger.info(f"找到 {len(dwg_files)} 个需要转换的DWG文件")
                
                # 逐一转换每个DWG文件
                for dwg_file in dwg_files:
                    order_id = dwg_file.get('id')
                    dwg_path = dwg_file.get('FilePath')
                    
                    if order_id and dwg_path:
                        logger.info(f"开始转换订单ID: {order_id} 的DWG文件: {dwg_path}")
                        await convert_dwg_from_database(order_id, dwg_path)
                    else:
                        logger.warning("找到无效的DWG文件记录: %s", dwg_file)
            else:
                logger.info("未找到需要转换的DWG文件")
            
        except Exception as e:
            logger.error(f"定期检查和转换任务出错: {str(e)}")
        
        # 等待指定的检查间隔
        logger.info(f"等待 {check_interval} 秒后再次检查")
        await asyncio.sleep(check_interval)

# 从数据库获取需要转换的DWG文件
def get_dwg_files_from_database():
    """从数据库查询需要转换的DWG文件"""
    try:
        # 用户提供的SQL查询
        query = """
            SELECT 
               o.id ,c.FilePath 
            FROM 
               c_order o 
            INNER JOIN C_Attachment c on c.RefId = o.id 
            WHERE 
               OrderStatus BETWEEN 60 and 160 and c.istopdf is null  AND c.FilePath LIKE '%.dwg'
        """
        
        results = db.execute_query(query)
        logger.info(f"查询数据库成功，返回 {len(results)} 条记录")
        return results
    except Exception as e:
        logger.error(f"查询数据库中的DWG文件失败: {str(e)}")
        return []

# 转换从数据库获取的DWG文件
async def convert_dwg_from_database(order_id, dwg_path, skip_exists_check=False):
    """转换从数据库获取的DWG文件，skip_exists_check=True时跳过文件存在性检查"""
    """转换从数据库获取的DWG文件"""
    try:
        # 从环境变量中获取DWG文件路径前缀
        dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
        
        # 拼接完整的DWG文件路径
        # 如果数据库中的路径已经是绝对路径（以驱动器字母或\开头），则不添加前缀
        if dwg_path.startswith('\\') or (len(dwg_path) >= 2 and dwg_path[1] == ':'):
            full_dwg_path = dwg_path
        else:
            # 如果路径前缀存在，并且路径不以\开头，则添加\
            if dwg_file_prefix and not dwg_path.startswith('\\'):
                full_dwg_path = dwg_file_prefix +  dwg_path
            else:
                full_dwg_path = os.path.join(dwg_file_prefix, dwg_path.lstrip('\\'))
        
        logger.info(f"原始DWG路径: {dwg_path}, 完整DWG路径: {full_dwg_path}")
        
        # 检查文件是否存在（除非跳过检查）
        dwg_file_path = Path(full_dwg_path)
        if not skip_exists_check and not dwg_file_path.exists():
            logger.error(f"DWG文件不存在: {full_dwg_path}")
            # 更新数据库状态，表示文件不存在
            update_conversion_status(order_id, full_dwg_path, "失败", "文件不存在")
            return
        
        # 生成PDF输出路径（与源文件相同目录）
        pdf_filename = f"{dwg_file_path.stem}.pdf"
        pdf_path = dwg_file_path.parent / pdf_filename
        
        logger.info(f"准备将DWG文件转换为PDF: {dwg_file_path} -> {pdf_path}")
        
        # 调用转换函数
        convert_with_autocad(dwg_file_path, pdf_path)
        
        # 验证PDF文件是否成功创建
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件未创建: {pdf_path}")
            
        # 获取文件大小
        pdf_size = pdf_path.stat().st_size
        if pdf_size == 0:
            raise ValueError(f"创建的PDF文件为空: {pdf_size} 字节")
            
        logger.info(f"成功将订单ID: {order_id} 的DWG文件转换为PDF，文件大小: {pdf_size} 字节")
        
        # 记录转换成功信息到数据库
        record_conversion_to_database(dwg_file_path.name, str(dwg_file_path), str(pdf_path), "成功", pdf_size)
        
        # 将生成的PDF文件插入到C_Attachment表
        # 使用数据库中的原始路径，因为C_Attachment表中存储的是原始路径
        insert_success = insert_pdf_to_attachment(order_id, str(pdf_path), dwg_path)
        if not insert_success:
            logger.warning(f"PDF文件转换成功，但插入到C_Attachment表失败: {pdf_path}")
        
        # 更新C_Attachment表中的istopdf字段，标记为已转换
        # 使用数据库中的原始路径，因为C_Attachment表中存储的是原始路径
        update_attachment_is_pdf(order_id, dwg_path)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"转换订单ID: {order_id} 的DWG文件失败: {error_msg}")
        
        # 记录转换失败信息到数据库
        record_conversion_to_database(dwg_file_path.name if 'dwg_file_path' in locals() else "未知", 
                                     str(dwg_path), "", "失败", 0, error_msg)

# 记录转换信息到conversion_history表
def record_conversion_to_database(file_name, original_path, pdf_path, status, file_size=0, error_message=""):
    """记录转换信息到conversion_history表
    
    特别处理：如果PDF文件为空（仅包含基本的PDF头信息），则不将其记录为成功状态
    """
    try:
        # 计算PDF文件的相对路径而不是使用绝对路径
        # 获取DWG_FILE_PREFIX环境变量作为基准路径
        import os
        from pathlib import Path
        
        dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
        relative_pdf_path = pdf_path
        
        # 如果设置了DWG_FILE_PREFIX，并且PDF路径不为空且以该前缀开头，则移除前缀
        if dwg_file_prefix and pdf_path and pdf_path.startswith(dwg_file_prefix):
            # 移除前缀并确保路径以斜杠开头
            relative_pdf_path = pdf_path[len(dwg_file_prefix):]
            # 确保路径以斜杠开头
            if relative_pdf_path and not relative_pdf_path.startswith('/') and not relative_pdf_path.startswith('\\'):
                relative_pdf_path = '/' + relative_pdf_path
            logger.info(f"已将绝对路径转换为相对路径: {relative_pdf_path}")
        elif pdf_path:
            # 如果无法基于DWG_FILE_PREFIX计算相对路径，但有原始路径信息，尝试从原始路径推断目录结构
            try:
                
                # 从原始路径获取目录结构
                if original_path and original_path.startswith(dwg_file_prefix):
                    # 获取原始文件的相对路径
                    relative_original_path = original_path[len(dwg_file_prefix):]
                    # 获取原始文件的目录结构
                    original_dir = os.path.dirname(relative_original_path)
                    
                    # 提取PDF文件名
                    pdf_filename = Path(pdf_path).name
                    
                    if original_dir:
                        # 构建与原始文件相同目录结构的PDF相对路径
                        relative_pdf_path = os.path.join(original_dir, pdf_filename)
                        # 确保路径以斜杠开头
                        if not relative_pdf_path.startswith('/') and not relative_pdf_path.startswith('\\'):
                            relative_pdf_path = '/' + relative_pdf_path
                        logger.info(f"基于原始路径推断的PDF相对路径: {relative_pdf_path}")
                    else:
                        # 回退到使用文件名部分
                        logger.warning(f"无法从原始路径推断目录结构，使用文件名部分")
                        relative_pdf_path = '/' + pdf_filename
                else:
                    # 如果原始路径不以DWG_FILE_PREFIX开头，使用文件名部分
                    pdf_filename = Path(pdf_path).name
                    relative_pdf_path = '/' + pdf_filename
            except Exception as e:
                logger.error(f"尝试从原始路径推断PDF路径时出错: {str(e)}")
                # 回退到使用文件名部分
                pdf_filename = Path(pdf_path).name
                relative_pdf_path = '/' + pdf_filename
        
        # 统一路径分隔符为斜杠（如果有路径的话）
        if relative_pdf_path:
            relative_pdf_path = relative_pdf_path.replace('\\', '/')
            
        # 检查是否为成功状态并且PDF文件存在
        if status == "成功" and pdf_path:
            # 检查PDF文件是否为空（仅包含基本的PDF头信息）
            try:
                # 检查文件是否存在
                if os.path.exists(pdf_path):
                    # 检查文件大小
                    actual_file_size = os.path.getsize(pdf_path)
                    
                    # 如果文件大小小于20字节，很可能是只有PDF头的空文件
                    if actual_file_size < 20:
                        logger.warning(f"PDF文件为空（仅包含头信息）: {pdf_path}，大小: {actual_file_size} 字节，不记录到数据库")
                        # 不记录到数据库，直接返回
                        return
                    
                    # 进一步检查文件内容
                    with open(pdf_path, 'rb') as f:
                        # 读取前20个字节
                        content = f.read(20)
                        
                    # 检查是否只有PDF头信息（"%PDF-1.4\n%"）
                    if content.startswith(b'%PDF-1.4\n%') and len(content.strip()) == 8:
                        logger.warning(f"PDF文件为空（仅包含头信息）: {pdf_path}，不记录到数据库")
                        # 不记录到数据库，直接返回
                        return
            except Exception as check_error:
                logger.warning(f"检查PDF文件内容时出错: {str(check_error)}")
                # 发生错误时，继续处理，让调用者决定是否记录
        
        if status == "成功":
            insert_query = """
                INSERT INTO conversion_history (file_name, original_path, pdf_path, status, file_size)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (file_name, original_path, relative_pdf_path, status, file_size)
        else:
            insert_query = """
                INSERT INTO conversion_history (file_name, original_path, pdf_path, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (file_name, original_path, relative_pdf_path, status, error_message)
        
        db.execute_query(insert_query, params)
        logger.info(f"转换记录已保存到数据库: {file_name}, 状态: {status}")
    except Exception as db_error:
        logger.error(f"保存转换记录到数据库失败: {str(db_error)}")

# 更新C_Attachment表中的istopdf字段
def update_attachment_is_pdf(order_id, file_path):
    """更新C_Attachment表中的istopdf字段，标记为已转换
    
    特别处理：如果PDF文件为空（仅包含基本的PDF头信息），则不更新istopdf字段
    """
    
    try:
        # 首先查找对应的PDF文件路径
        # 查询原始DWG文件的记录，获取对应的PDF文件路径
        dwg_record = get_dwg_attachment_record(order_id, file_path)
        
        if dwg_record:
            # 构建对应的PDF文件路径
            # 假设PDF文件与DWG文件在同一目录，只是扩展名不同
            import os
            pdf_path = os.path.splitext(file_path)[0] + '.pdf'
            
            # 检查PDF文件是否存在
            if os.path.exists(pdf_path):
                # 检查文件大小
                pdf_file_size = os.path.getsize(pdf_path)
                
                # 如果文件大小小于20字节，很可能是只有PDF头的空文件，不更新istopdf字段
                if pdf_file_size < 20:
                    logger.warning(f"PDF文件为空（仅包含头信息）: {pdf_path}，大小: {pdf_file_size} 字节，不更新istopdf字段")
                    return
    except Exception as check_error:
        logger.warning(f"检查PDF文件时出错: {str(check_error)}")
        # 发生错误时，继续更新，避免因检查错误而影响主流程
    
    # 执行更新操作
    try:
        update_query = """
            UPDATE C_Attachment
            SET istopdf = 1
            WHERE RefId = ? AND FilePath = ?
        """
        affected_rows = db.execute_query(update_query, (order_id, file_path))
        logger.info(f"已更新C_Attachment表，标记文件为已转换，受影响行数: {affected_rows}")
    except Exception as db_error:
        logger.error(f"更新C_Attachment表失败: {str(db_error)}")

# 将生成的PDF文件插入到C_Attachment表
def insert_pdf_to_attachment(order_id, pdf_path, original_dwg_path):
    """将生成的PDF文件插入到C_Attachment表中
    
    特别处理：如果PDF文件为空（仅包含基本的PDF头信息），则不将其插入到数据库
    """
    try:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            logger.error(f"PDF文件不存在，无法插入到数据库: {pdf_path}")
            return False
        
        # 检查PDF文件是否为空（仅包含基本的PDF头信息）
        try:
            # 检查文件大小
            actual_file_size = pdf_file.stat().st_size
            
            # 如果文件大小小于20字节，很可能是只有PDF头的空文件
            if actual_file_size < 20:
                logger.warning(f"PDF文件为空（仅包含头信息）: {pdf_path}，大小: {actual_file_size} 字节，不插入到C_Attachment表")
                # 不插入到数据库，直接返回
                return False
            
            # 进一步检查文件内容
            with open(pdf_path, 'rb') as f:
                # 读取前20个字节
                content = f.read(20)
                
            # 检查是否只有PDF头信息（"%PDF-1.4\n%"）
            if content.startswith(b'%PDF-1.4\n%') and len(content.strip()) == 8:
                logger.warning(f"PDF文件为空（仅包含头信息）: {pdf_path}，不插入到C_Attachment表")
                # 不插入到C_Attachment表，直接返回
                return False
        except Exception as check_error:
            logger.warning(f"检查PDF文件内容时出错: {str(check_error)}")
            # 发生错误时，继续处理，让调用者决定是否记录
            
        # 获取PDF文件信息
        pdf_filename = pdf_file.name
        
        # 获取当前时间作为创建时间
        import datetime
        current_time = datetime.datetime.now()
        
        # 从原始DWG文件记录获取相关信息（如AttachmentType、GroupGuid等）
        # 首先查询原始DWG文件的记录
        dwg_record = get_dwg_attachment_record(order_id, original_dwg_path)
        
        if dwg_record:
            attachment_type = dwg_record.get('AttachmentType', 1)  # 默认值为1
            created_by = dwg_record.get('CreatedBy', 'DWG2PDF API')
            group_guid = dwg_record.get('GroupGuid')
            tag = dwg_record.get('Tag')
            version = dwg_record.get('Version', 1)
            logger.info(f"已获取原始DWG文件的记录信息，AttachmentType: {attachment_type}, GroupGuid: {group_guid}")
        else:
            # 如果没有找到原始DWG记录，使用默认值
            attachment_type = 1
            created_by = 'DWG2PDF API'
            group_guid = None
            tag = 'DWG转PDF'
            version = 1
            logger.warning(f"未找到原始DWG文件的记录，使用默认值: {original_dwg_path}")
        
        # 计算相对路径而不是使用绝对路径
        # 获取DWG_FILE_PREFIX环境变量作为基准路径
        dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
        relative_pdf_path = str(pdf_path)
        
        # 如果设置了DWG_FILE_PREFIX，并且PDF路径以该前缀开头，则移除前缀
        if dwg_file_prefix and relative_pdf_path.startswith(dwg_file_prefix):
            # 移除前缀并确保路径以斜杠开头
            relative_pdf_path = relative_pdf_path[len(dwg_file_prefix):]
            # 确保路径以斜杠开头
            if not relative_pdf_path.startswith('/') and not relative_pdf_path.startswith('\\'):
                relative_pdf_path = '/' + relative_pdf_path
            logger.info(f"已将绝对路径转换为相对路径: {relative_pdf_path}")
        else:
            # 如果无法基于DWG_FILE_PREFIX计算相对路径，但有原始DWG文件的记录，尝试从原始DWG路径推断
            if dwg_record and 'FilePath' in dwg_record:
                original_dwg_relative_path = dwg_record['FilePath']
                # 保留原始DWG文件的目录结构，只替换文件名
                dwg_dir_in_db = os.path.dirname(original_dwg_relative_path)
                if dwg_dir_in_db:
                    relative_pdf_path = os.path.join(dwg_dir_in_db, pdf_filename)
                    # 确保路径以斜杠开头
                    if not relative_pdf_path.startswith('/') and not relative_pdf_path.startswith('\\'):
                        relative_pdf_path = '/' + relative_pdf_path
                    logger.info(f"基于原始DWG路径推断的相对路径: {relative_pdf_path}")
                else:
                    # 回退到使用文件名部分
                    logger.warning(f"无法从原始DWG路径推断目录结构，使用文件名部分")
                    relative_pdf_path = '/' + pdf_filename
            else:
                # 如果没有原始DWG记录，记录警告并使用原始路径的文件名部分
                logger.warning(f"无法基于DWG_FILE_PREFIX({dwg_file_prefix})计算相对路径且无原始DWG记录，使用文件名部分")
                relative_pdf_path = '/' + pdf_filename
            
        # 统一路径分隔符为斜杠
        relative_pdf_path = relative_pdf_path.replace('\\', '/')
        
        # 插入PDF文件到C_Attachment表
        # 使用从表结构检查中获取的实际字段名
        insert_query = """
            INSERT INTO C_Attachment (
                RefId, 
                AttachmentType, 
                FileName, 
                FilePath, 
                CreatedBy, 
                CreatedDateTime, 
                GroupGuid, 
                Tag, 
                Version, 
                istopdf
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            order_id,  # RefId: 订单ID
            attachment_type,  # AttachmentType: 附件类型，与原始DWG相同或使用默认值
            pdf_filename,  # FileName: PDF文件名
            relative_pdf_path,  # FilePath: PDF文件相对路径
            created_by,  # CreatedBy: 创建者
            current_time,  # CreatedDateTime: 创建时间
            group_guid,  # GroupGuid: 分组GUID，与原始DWG相同
            tag,  # Tag: 标签
            version,  # Version: 版本号
            1  # istopdf: 标记为PDF文件
        )
        
        affected_rows = db.execute_query(insert_query, params)
        logger.info(f"已将PDF文件插入到C_Attachment表，文件名: {pdf_filename}，受影响行数: {affected_rows}")
        return True
        
    except Exception as db_error:
        logger.error(f"将PDF文件插入到C_Attachment表失败: {str(db_error)}")
        return False

# 获取原始DWG文件的附件记录
def get_dwg_attachment_record(order_id, dwg_path):
    """从C_Attachment表获取原始DWG文件的记录信息"""
    try:
        # 查询原始DWG文件的记录
        query = """
            SELECT TOP 1 * 
            FROM C_Attachment 
            WHERE RefId = ? AND FilePath = ?
            ORDER BY Id DESC
        """
        
        results = db.execute_query(query, (order_id, dwg_path))
        
        if results and len(results) > 0:
            logger.info(f"找到原始DWG文件的记录: {dwg_path}")
            return results[0]
        else:
            logger.warning(f"未找到原始DWG文件的记录: {dwg_path}")
            return None
            
    except Exception as e:
        logger.error(f"查询原始DWG文件记录失败: {str(e)}")
        return None

# 更新转换状态
def update_conversion_status(order_id, file_path, status, error_message=""):
    """更新转换状态，在实际应用中可能需要额外的表来跟踪状态"""
    try:
        # 这里可以添加更新状态的逻辑，例如更新一个专门的状态表
        logger.info(f"更新订单ID: {order_id} 的转换状态为: {status}")
        
        # 同时更新istopdf字段为-1表示处理失败
        if status == "失败":
            update_query = """
                UPDATE C_Attachment
                SET istopdf = -1
                WHERE RefId = ? AND FilePath = ?
            """
            affected_rows = db.execute_query(update_query, (order_id, file_path))
            logger.info(f"已更新C_Attachment表，标记文件处理失败，受影响行数: {affected_rows}")
    except Exception as db_error:
        logger.error(f"更新转换状态失败: {str(db_error)}")


# API端点：手动触发数据库查询和转换任务
@app.post("/convert/database", tags=["数据库转换"])
async def convert_from_database(skip_exists_check: bool = False):
    """手动触发从数据库查询DWG文件并进行转换的任务
    
    参数:
    - skip_exists_check: 是否跳过文件存在性检查
    
    返回:
    - 任务执行状态和统计信息
    """
    try:
        logger.info(f"收到手动触发数据库转换任务的请求，skip_exists_check: {skip_exists_check}")
        
        # 执行查询获取需要转换的DWG文件
        dwg_files = get_dwg_files_from_database()
        
        if not dwg_files:
            logger.info("未找到需要转换的DWG文件")
            return {
                "status": "success",
                "message": "未找到需要转换的DWG文件",
                "total_files": 0,
                "converted_files": 0,
                "failed_files": 0
            }
        
        logger.info(f"找到 {len(dwg_files)} 个需要转换的DWG文件")
        
        # 统计信息
        stats = {
            "total_files": len(dwg_files),
            "converted_files": 0,
            "failed_files": 0,
            "failed_files_details": []
        }
        
        # 逐一转换每个DWG文件
        for dwg_file in dwg_files:
            order_id = dwg_file.get('id')
            dwg_path = dwg_file.get('FilePath')
            
            if order_id and dwg_path:
                logger.info(f"开始转换订单ID: {order_id} 的DWG文件: {dwg_path}")
                try:
                    # 转换文件，传递skip_exists_check参数
                    await convert_dwg_from_database(order_id, dwg_path, skip_exists_check)
                    stats["converted_files"] += 1
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"转换订单ID: {order_id} 的DWG文件失败: {error_msg}")
                    stats["failed_files"] += 1
                    stats["failed_files_details"].append({
                        "order_id": order_id,
                        "file_path": dwg_path,
                        "error": error_msg
                    })
            else:
                logger.warning(f"找到无效的DWG文件记录: {dwg_file}")
                stats["failed_files"] += 1
                
        logger.info(f"手动触发数据库转换任务完成: 总计 {stats['total_files']} 个文件，成功 {stats['converted_files']} 个，失败 {stats['failed_files']} 个")
        
        return {
            "status": "success",
            "message": f"数据库转换任务执行完成",
            "total_files": stats["total_files"],
            "converted_files": stats["converted_files"],
            "failed_files": stats["failed_files"],
            "failed_files_details": stats["failed_files_details"] if stats["failed_files"] > 0 else None
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"手动触发数据库转换任务失败: {error_msg}")
        raise HTTPException(status_code=500, detail=f"执行数据库转换任务失败: {error_msg}")

  
  # 在应用关闭事件中关闭数据库连接
@app.on_event("shutdown")
async def shutdown_event():
    try:
        db.disconnect()
        logger.info("应用已关闭，数据库连接已断开")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {str(e)}")

# 从环境变量获取临时目录配置，如果不存在则使用默认值
TEMP_DIR_PATH = os.getenv("TEMP_DIR", "temp")
# 确保临时目录存在，使用绝对路径
TEMP_DIR = Path(os.path.abspath(TEMP_DIR_PATH))
TEMP_DIR.mkdir(exist_ok=True)
logger.info(f"使用临时目录: {TEMP_DIR}")



@app.post("/convert/dwg-to-pdf", response_class=FileResponse)
async def convert_dwg_to_pdf(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """将DWG文件转换为PDF格式"""
    # 验证文件类型
    if not file.filename.lower().endswith(".dwg"):
        raise HTTPException(status_code=400, detail="仅支持DWG文件")
    
    try:
        # 保存上传的DWG文件到临时目录
        temp_filename = next(tempfile._get_candidate_names())
        dwg_path = TEMP_DIR / f"{temp_filename}.dwg"
        with open(dwg_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 验证文件是否成功保存
        if not dwg_path.exists():
            raise FileNotFoundError(f"无法保存上传的文件到: {dwg_path}")
        
        # 使用当前工作目录作为PDF输出路径，避免权限和路径解析问题
        pdf_path = Path(os.getcwd()) / f"{temp_filename}.pdf"
        logger.info(f"PDF输出路径设置为当前目录: {pdf_path}")
        
        logger.info(f"已保存上传文件到: {dwg_path}")
        
        # 使用新创建的包来转换DWG到PDF
        success = converter_dwg_to_pdf(str(dwg_path), str(pdf_path))
        
        # 验证PDF文件是否成功创建
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件未创建: {pdf_path}")
            
        # 获取文件大小作为额外验证
        pdf_size = pdf_path.stat().st_size
        if pdf_size == 0:
            raise ValueError(f"创建的PDF文件为空: {pdf_size} 字节")
            
        logger.info(f"成功将 {file.filename} 转换为PDF，文件大小: {pdf_size} 字节")
        
        # 记录转换成功信息到数据库
        try:
            insert_query = """
                INSERT INTO conversion_history (file_name, original_path, pdf_path, status, file_size)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_query(
                insert_query,
                (file.filename, str(dwg_path), str(pdf_path), "成功", pdf_size)
            )
            logger.info("转换记录已保存到数据库")
        except Exception as db_error:
            logger.error(f"保存转换记录到数据库失败: {str(db_error)}")
        
        # 添加后台任务，在响应返回后清理临时文件
        def cleanup_files():
            import time
            cleanup_delay = 300  # 延迟30秒清理文件，确保文件传输完成
            logger.info(f"等待{cleanup_delay}秒后开始清理文件，确保文件传输完成...")
            time.sleep(cleanup_delay)
            
            # 清理DWG文件
            if dwg_path and hasattr(dwg_path, 'exists') and dwg_path.exists():
                try:
                    dwg_path.unlink()
                    logger.info(f"已清理临时DWG文件: {dwg_path}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时DWG文件失败: {str(cleanup_error)}")
            
            # 清理PDF文件 - 检查当前工作目录和临时目录
            pdf_basename = None
            if pdf_path and hasattr(pdf_path, 'name'):
                pdf_basename = pdf_path.name
            
            # 检查可能的PDF文件位置
            pdf_locations = []
            if pdf_path:
                pdf_locations.append(pdf_path)
            if pdf_basename:
                pdf_locations.append(Path(os.getcwd()) / pdf_basename)
                pdf_locations.append(TEMP_DIR / pdf_basename)
                pdf_locations.append(Path(os.environ.get('TEMP', '')) / pdf_basename)
            
            # 尝试清理所有可能的PDF文件
            for location in pdf_locations:
                if hasattr(location, 'exists') and location.exists():
                    try:
                        location.unlink()
                        logger.info(f"已清理PDF文件: {location}")
                    except Exception as cleanup_error:
                        logger.warning(f"清理PDF文件失败: {location}，错误: {str(cleanup_error)}")
            
            if not any(hasattr(loc, 'exists') and loc.exists() for loc in pdf_locations):
                logger.info(f"未找到需要清理的PDF文件，文件基础名: {pdf_basename}")
        
        # 注册后台清理任务
        background_tasks.add_task(cleanup_files)
        
        # 在返回前等待并验证PDF文件是否存在
        import time
        max_wait_time = 30  # 最大等待时间（秒）
        check_interval = 0.5  # 检查间隔（秒）
        waited_time = 0
        
        # 循环检查文件是否存在、大小大于最小阈值且稳定（不再变化）
        stable_size_count = 0
        required_stable_checks = 3  # 需要连续3次检测到相同大小才算稳定
        last_size = -1
        MIN_PDF_SIZE = 500  # 设置最小PDF文件大小阈值（字节）
        
        while waited_time < max_wait_time:
            if pdf_path.exists():
                pdf_size = pdf_path.stat().st_size
                
                # 检查文件大小是否大于最小阈值
                if pdf_size >= MIN_PDF_SIZE:
                    # 检查文件大小是否稳定（不再变化）
                    if pdf_size == last_size:
                        stable_size_count += 1
                        logger.info(f"PDF文件大小稳定({stable_size_count}/{required_stable_checks}): {pdf_path}，大小: {pdf_size} 字节")
                        
                        # 如果文件大小连续稳定了指定次数，认为文件已完全写入完成
                        if stable_size_count >= required_stable_checks:
                            logger.info(f"PDF文件已完全生成并准备提供服务: {pdf_path}，大小: {pdf_size} 字节")
                            break
                    else:
                        # 文件大小仍在变化，重置稳定计数
                        stable_size_count = 0
                        last_size = pdf_size
                        logger.info(f"PDF文件正在生成中，当前大小: {pdf_size} 字节，等待: {waited_time:.1f}秒")
                elif pdf_size > 0:
                    # 文件大小小于最小阈值，可能是临时文件或空文件头
                    logger.warning(f"PDF文件大小过小（{pdf_size}字节），可能不是有效的PDF文件，继续等待... 当前等待: {waited_time:.1f}秒")
                    # 不增加稳定计数，继续等待文件增长
                    last_size = pdf_size
                else:
                    logger.info(f"PDF文件已存在但大小为0，等待文件写入完成... 当前等待: {waited_time:.1f}秒")
            else:
                logger.info(f"PDF文件尚未生成，等待中... 当前等待: {waited_time:.1f}秒")
            
            time.sleep(check_interval)
            waited_time += check_interval
        
        # 再次验证文件是否存在且大小符合要求
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件在等待{max_wait_time}秒后仍未生成: {pdf_path}")
        
        pdf_size = pdf_path.stat().st_size
        if pdf_size < MIN_PDF_SIZE:
            raise ValueError(f"PDF文件大小过小（{pdf_size}字节），可能不是有效的PDF文件: {pdf_path}")
        
        logger.info(f"返回文件路径: {str(pdf_path)}")
        # 导入URL编码模块
        import urllib.parse
        
        # 对文件名进行URL编码，解决中文文件名在HTTP头部的编码问题
        encoded_filename = urllib.parse.quote(f"{file.filename.rsplit('.', 1)[0]}.pdf")
        
        # 返回转换后的PDF文件，使用正确的HTTP头
        return FileResponse(
            path=str(pdf_path),  # 直接使用字符串路径
            filename=f"{file.filename.rsplit('.', 1)[0]}.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={encoded_filename}"
                # 注意：filename*参数在某些浏览器中可能需要，但大多数现代浏览器支持filename参数的UTF-8编码
            }
        )
        
    except Exception as e:
        logger.error(f"转换文件时出错: {str(e)}")
        
        # 记录转换失败信息到数据库
        try:
            if 'file' in locals() and 'dwg_path' in locals() and hasattr(dwg_path, '__str__'):
                insert_query = """
                INSERT INTO conversion_history (file_name, original_path, pdf_path, status, error_message)
                VALUES (?, ?, ?, ?, ?)
                """
                pdf_path_str = str(pdf_path) if 'pdf_path' in locals() and hasattr(pdf_path, '__str__') else ""
                db.execute_query(
                    insert_query,
                    (file.filename, str(dwg_path), pdf_path_str, "失败", str(e))
                )
                logger.info("转换失败记录已保存到数据库")
        except Exception as db_error:
            logger.error(f"保存转换失败记录到数据库失败: {str(db_error)}")
        # 转换失败时立即清理临时文件
        if 'dwg_path' in locals() and dwg_path.exists():
            dwg_path.unlink()
        if 'pdf_path' in locals() and pdf_path.exists():
            pdf_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


def safe_com_call(func, *args):
    """安全地调用COM接口函数，处理编码问题和COM异常
    解决Windows系统下AutoCAD COM接口的'latin-1'编码问题和各种COM异常
    """
    try:
        # 处理COM接口调用前，确保所有路径参数使用正确的编码
        encoded_args = []
        for arg in args:
            if isinstance(arg, str):
                # 确保路径作为原生Unicode字符串传递给COM接口
                encoded_args.append(arg)
            else:
                encoded_args.append(arg)
        
        # 特殊处理PlotToFile调用，避免被错误识别为属性设置
        if hasattr(func, '__name__') and func.__name__ == 'PlotToFile':
            # 使用动态方法调用方式
            logger.info("使用特殊处理的PlotToFile调用方式")
            # 从函数对象获取所属实例和方法名
            instance = func.__self__
            method_name = func.__name__
            # 使用getattr和动态调用
            result = getattr(instance, method_name)(*encoded_args)
            return result
        
        # 尝试调用COM接口函数
        result = func(*encoded_args)
        return result
    except Exception as e:
        # 尝试捕获并处理编码错误和常见COM异常
        error_msg = str(e)
        
        # 特殊处理'latin-1'编码错误
        if "'latin-1' codec can't encode" in error_msg:
            # 检查参数中是否有包含非ASCII字符的路径
            for i, arg in enumerate(args):
                if isinstance(arg, str) and any(ord(c) > 127 for c in arg):
                    logger.error(f"参数 {i} 包含非ASCII字符: {arg}")
                    # 尝试使用一个完全不同的方法来处理包含中文的路径
                    # 1. 将文件复制到纯ASCII路径的临时文件
                    import tempfile
                    import shutil
                    temp_dir = tempfile.gettempdir()
                    ascii_name = ''.join(c if ord(c) < 128 else 'x' for c in os.path.basename(arg))
                    temp_path = os.path.join(temp_dir, ascii_name)
                    logger.info(f"尝试将包含非ASCII字符的文件复制到ASCII路径: {temp_path}")
                    try:
                        shutil.copy2(arg, temp_path)
                        logger.info(f"文件复制成功: {arg} -> {temp_path}")
                        
                        # 2. 重新构建参数列表，用ASCII路径替换原路径
                        new_args = list(args)
                        new_args[i] = temp_path
                        
                        # 3. 使用ASCII路径重新尝试COM调用
                        logger.info(f"使用ASCII路径重新尝试COM调用: {temp_path}")
                        result = func(*new_args)
                        
                        # 4. 如果是输出文件，在调用成功后复制回原位置
                        if func.__name__ == 'PlotToFile' and i == 0:
                            logger.info(f"将生成的文件从ASCII路径复制回原位置: {temp_path} -> {new_args[0]}")
                            shutil.copy2(temp_path, new_args[0])
                        
                        # 5. 清理临时文件
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        
                        return result
                    except Exception as copy_error:
                        logger.error(f"复制文件到ASCII路径失败: {str(copy_error)}")
                        # 如果复制失败，继续抛出原始异常
        # 特殊处理常见的COM调用失败错误，如(-2147352567, '发生意外。')
        elif "-2147352567" in error_msg or "发生意外" in error_msg:
            logger.error(f"COM调用失败，尝试重新初始化COM接口...")
            try:
                # 尝试重新初始化COM接口
                import pythoncom
                pythoncom.CoUninitialize()
                pythoncom.CoInitialize()
                logger.info("COM接口已重新初始化")
                
                # 重新尝试调用
                logger.info(f"重新尝试COM调用...")
                result = func(*encoded_args)
                return result
            except Exception as retry_error:
                logger.error(f"重新尝试COM调用失败: {str(retry_error)}")
                # 如果重试失败，继续抛出原始异常
        
        try:
            # 尝试重新编码错误信息，避免'latin-1'编码问题
            error_msg = error_msg.encode('utf-8').decode('utf-8')
        except:
            pass
        raise Exception(f"COM调用失败: {error_msg}")


def convert_with_autocad(dwg_path: Path, pdf_path: Path):
    """使用AutoCAD COM接口将DWG文件转换为PDF"""
    logger.info("使用基础版本的DWG到PDF转换函数")
    
    # 直接调用基础版本的转换函数
    convert_with_autocad_basic(dwg_path, pdf_path)
    
    logger.info(f"DWG到PDF转换完成: {dwg_path} -> {pdf_path}")

@app.get("/")
async def root():
    """API根端点，提供基本信息"""
    return {
        "message": "欢迎使用DWG到PDF转换器API",
        "endpoints": [
            "/convert/dwg-to-pdf (POST) - 上传DWG文件转换为PDF",
            "/conversion-history (GET) - 获取转换历史记录",
            "/convert/database (POST) - 手动触发从数据库查询DWG文件并进行转换的任务"
        ]
    }


@app.get("/conversion-history")
async def get_conversion_history(page: int = 1, page_size: int = 20, status: str = None):
    """获取转换历史记录
    
    参数:
    - page: 页码（默认为1）
    - page_size: 每页记录数（默认为20）
    - status: 过滤状态（可选：成功/失败）
    """
    try:
        offset = (page - 1) * page_size
        query_parts = [
            "SELECT id, file_name, original_path, pdf_path, conversion_time, status, file_size, error_message",
            "FROM conversion_history",
            "WHERE 1=1"
        ]
        params = []
        
        # 添加状态过滤条件
        if status:
            query_parts.append("AND status = ?")
            params.append(status)
        
        # 添加排序和分页
        query_parts.append("ORDER BY conversion_time DESC")
        query_parts.append(f"OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY")
        
        # 执行查询获取数据
        query = "\n".join(query_parts)
        results = db.execute_query(query, params)
        
        # 查询总记录数
        count_query = "SELECT COUNT(*) AS total FROM conversion_history WHERE 1=1"
        if status:
            count_query += " AND status = ?"
        total_result = db.execute_query(count_query, params if status else None)
        total_count = total_result[0]['total'] if total_result else 0
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "data": results
        }
    except Exception as e:
        logger.error(f"获取转换历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取转换历史记录失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # 从环境变量获取主机和端口配置
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8007"))
    uvicorn.run(app, host=host, port=port)
