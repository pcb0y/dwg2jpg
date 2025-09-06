import os
from pathlib import Path
from dotenv import load_dotenv
import pyodbc
import os
from typing import List, Dict, Any, Optional
from logger_config import logger

# 加载.env文件中的环境变量
load_dotenv()
class SQLDatabase:
    """SQL数据库连接和操作类"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.conn = None
        self.connect()
    
    def connect(self):
        """建立数据库连接"""
        try:
            # 从环境变量获取数据库连接信息
            server = os.getenv("DB_SERVER", "localhost")
            database = os.getenv("DB_DATABASE", "test_db")
            username = os.getenv("DB_USERNAME", "sa")
            password = os.getenv("DB_PASSWORD", "password")
            driver = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")
            
            # 构建连接字符串
            conn_str = (
                f"DRIVER={driver};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                "TrustServerCertificate=yes;"
            )
            
            # 建立连接
            self.conn = pyodbc.connect(conn_str)
            logger.info(f"成功连接到数据库: {server}/{database}")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            self.conn = None
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行SQL查询并返回结果
        
        参数:
        - query: SQL查询语句
        - params: 查询参数（可选）
        
        返回:
        - 查询结果列表
        """
        try:
            # 检查连接是否有效，如果无效则重新连接
            if not self.conn or self.conn.closed:
                self.connect()
                if not self.conn or self.conn.closed:
                    raise Exception("无法建立数据库连接")
            
            # 执行查询
            with self.conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # 如果是SELECT查询，获取结果
                if query.strip().upper().startswith("SELECT"):
                    # 获取列名
                    columns = [column[0] for column in cursor.description]
                    # 将结果转换为字典列表
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                # 如果是其他查询，返回受影响的行数
                else:
                    # 提交事务
                    self.conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"执行SQL查询失败: {str(e)}")
            logger.error(f"查询: {query}")
            logger.error(f"参数: {params}")
            # 如果是SELECT查询，返回空列表；否则返回0
            if query.strip().upper().startswith("SELECT"):
                return []
            else:
                return 0
    
    def disconnect(self):
        """关闭数据库连接"""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
                logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接时出错: {str(e)}")

# 创建全局数据库实例
db = SQLDatabase()

# 数据库操作函数
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
               OrderStatus BETWEEN 60 and 160 and c.istojpg is null  AND c.FilePath LIKE '%.dwg'
        """
        
        results = db.execute_query(query)
        logger.info(f"查询数据库成功，返回 {len(results)} 条记录")
        return results
    except Exception as e:
        logger.error(f"查询数据库中的DWG文件失败: {str(e)}")
        return []

def record_conversion_to_database(file_name, original_path, jpg_path, status, file_size=0, error_message=""):
    """记录转换信息到conversion_history表"""
    try:
        # 计算PDF文件的相对路径而不是使用绝对路径
        import os
        from pathlib import Path
        
        dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
        relative_jpg_path = jpg_path
        
        # 如果设置了DWG_FILE_PREFIX，并且PDF路径不为空且以该前缀开头，则移除前缀
        if dwg_file_prefix and jpg_path and jpg_path.startswith(dwg_file_prefix):
            # 移除前缀并确保路径以斜杠开头
            relative_jpg_path = jpg_path[len(dwg_file_prefix):]
            # 确保路径以斜杠开头
            if relative_jpg_path and not relative_jpg_path.startswith('/') and not relative_jpg_path.startswith('\\'):
                relative_jpg_path = '/' + relative_jpg_path
            logger.info(f"已将绝对路径转换为相对路径: {relative_jpg_path}")
        elif jpg_path:      
            # 如果无法基于DWG_FILE_PREFIX计算相对路径，但有原始路径信息，尝试从原始路径推断目录结构
            try:
                
                # 从原始路径获取目录结构
                if original_path and original_path.startswith(dwg_file_prefix):
                    # 获取原始文件的相对路径
                    relative_original_path = original_path[len(dwg_file_prefix):]
                    # 获取原始文件的目录结构
                    original_dir = os.path.dirname(relative_original_path)
                    
                    # 提取JPG文件名
                    jpg_filename = Path(jpg_path).name
                    
                    if original_dir:
                        # 构建与原始文件相同目录结构的JPG相对路径
                        relative_jpg_path = os.path.join(original_dir, jpg_filename)
                        # 确保路径以斜杠开头
                        if not relative_jpg_path.startswith('/') and not relative_jpg_path.startswith('\\'):
                            relative_jpg_path = '/' + relative_jpg_path
                        logger.info(f"基于原始路径推断的JPG相对路径: {relative_jpg_path}")
                    else:
                        # 回退到使用文件名部分
                        logger.warning(f"无法从原始路径推断目录结构，使用文件名部分")
                        relative_jpg_path = '/' + jpg_filename
                else:
                    # 如果原始路径不以DWG_FILE_PREFIX开头，使用文件名部分
                    jpg_filename = Path(jpg_path).name
                    relative_jpg_path = '/' + jpg_filename
            except Exception as e:
                logger.error(f"尝试从原始路径推断JPG路径时出错: {str(e)}")
                # 回退到使用文件名部分
                jpg_filename = Path(jpg_path).name
                relative_jpg_path = '/' + jpg_filename  
        
        # 统一路径分隔符为斜杠（如果有路径的话）
        if relative_jpg_path:
            relative_jpg_path = relative_jpg_path.replace('\\', '/')
            
        # 检查是否为成功状态并且PDF文件存在
        if status == "成功" and jpg_path:
            # 检查PDF文件是否为空（仅包含基本的PDF头信息）
            try:
                # 检查文件是否存在
                if os.path.exists(jpg_path):
                    # 检查文件大小
                    actual_file_size = os.path.getsize(jpg_path)
                    
                    # 如果文件大小小于20字节，很可能是只有PDF头的空文件
                    if actual_file_size < 20:
                        logger.warning(f"JPG文件为空（仅包含头信息）: {jpg_path}，大小: {actual_file_size} 字节，不记录到数据库")
                        # 不记录到数据库，直接返回
                        return
                    
                    # 进一步检查文件内容
                    with open(jpg_path, 'rb') as f:
                        # 读取前20个字节
                        content = f.read(20)
                        
                    # 检查是否只有jpg头信息（"%jpg-1.4\n%"）
                    if content.startswith(b'%jpg-1.4\n%') and len(content.strip()) == 8:
                        logger.warning(f"JPG文件为空（仅包含头信息）: {jpg_path}，不记录到数据库")
                        # 不记录到数据库，直接返回
                        return
            except Exception as check_error:
                logger.warning(f"检查JPG文件内容时出错: {str(check_error)}")
                # 发生错误时，继续处理，让调用者决定是否记录
        
        if status == "成功":
            insert_query = """
                INSERT INTO conversion_history (file_name, original_path, jpg_path, status, file_size)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (file_name, original_path, relative_jpg_path, status, file_size)
        else:
            insert_query = """
                INSERT INTO conversion_history (file_name, original_path, jpg_path, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (file_name, original_path, relative_jpg_path, status, error_message)
        
        db.execute_query(insert_query, params)
        logger.info(f"转换记录已保存到数据库: {file_name}, 状态: {status}")
    except Exception as db_error:
        logger.error(f"保存转换记录到数据库失败: {str(db_error)}")

def update_attachment_is_jpg(order_id, file_path):
    """更新C_Attachment表中的istojpg字段，标记为已转换（注意：istojpg是历史遗留字段名，实际存储的是JPG转换状态）"""
    
    try:
        # 首先查找对应的jpg文件路径
        # 查询原始DWG文件的记录，获取对应的PDF文件路径
        dwg_record = get_dwg_attachment_record(order_id, file_path)
        
        if dwg_record:
            # 构建对应的jpg文件路径
            # 假设PDF文件与DWG文件在同一目录，只是扩展名不同
            import os
            jpg_path = os.path.splitext(file_path)[0] + '.jpg'
            
            # 检查jpg文件是否存在
            if os.path.exists(jpg_path):
                # 检查文件大小
                jpg_file_size = os.path.getsize(jpg_path)
                
                # 如果文件大小小于20字节，很可能是只有jpg头的空文件，不更新istojpg字段
                if jpg_file_size < 20:
                    logger.warning(f"jpg文件为空（仅包含头信息）: {jpg_path}，大小: {jpg_file_size} 字节，不更新istojpg字段")
                    return
    except Exception as check_error:
        logger.warning(f"检查JPG文件时出错: {str(check_error)}")
        # 发生错误时，继续更新，避免因检查错误而影响主流程
    
    # 执行更新操作
    try:
        update_query = """
            UPDATE C_Attachment
            SET istojpg = 1
            WHERE RefId = ? AND FilePath = ?
        """
        affected_rows = db.execute_query(update_query, (order_id, file_path))
        logger.info(f"已更新C_Attachment表，标记文件为已转换，受影响行数: {affected_rows}")
    except Exception as db_error:
        logger.error(f"更新C_Attachment表失败: {str(db_error)}")

def insert_jpg_to_attachment(order_id, jpg_path, original_dwg_path):
    """将生成的JPG文件插入到C_Attachment表中"""
    try:
        jpg_file = Path(jpg_path)
        if not jpg_file.exists():
            logger.error(f"JPG文件不存在，无法插入到数据库: {jpg_path}")
            return False
        
        # 检查JPG文件是否为空
        try:
            # 检查文件大小
            actual_file_size = jpg_file.stat().st_size
            
            # 如果文件大小小于20字节，很可能是空文件
            if actual_file_size < 20:
                logger.warning(f"JPG文件为空: {jpg_path}，大小: {actual_file_size} 字节，不插入到C_Attachment表")
                # 不插入到数据库，直接返回
                return False
            
            # 进一步检查文件内容是否为JPG格式
            with open(jpg_path, 'rb') as f:
                # 读取前几个字节检查JPG文件头
                content = f.read(4)
                
                # 检查JPG文件头是否正确
                if content.startswith(b'\xff\xd8\xff'):
                    logger.info(f"JPG文件内容正确: {jpg_path}")
                else:
                    logger.warning(f"JPG文件内容错误，可能不是有效的JPG文件: {jpg_path}")
                    # 不插入到数据库，直接返回
                    return False
        except Exception as check_error:
            logger.warning(f"检查JPG文件内容时出错: {str(check_error)}")
            # 发生错误时，继续处理，让调用者决定是否记录
        
        # 获取JPG文件信息
        jpg_filename = jpg_file.name
        
        # 获取当前时间作为创建时间
        import datetime
        current_time = datetime.datetime.now()
        
        # 从原始DWG文件记录获取相关信息（如AttachmentType、GroupGuid等）
        # 首先查询原始DWG文件的记录
        dwg_record = get_dwg_attachment_record(order_id, original_dwg_path)
        
        if dwg_record:
            attachment_type = dwg_record.get('AttachmentType', 1)  # 默认值为1
            created_by = dwg_record.get('CreatedBy', 'DWG2JPG API')
            group_guid = dwg_record.get('GroupGuid')
            tag = dwg_record.get('Tag')
            version = dwg_record.get('Version', 1)
            logger.info(f"已获取原始DWG文件的记录信息，AttachmentType: {attachment_type}, GroupGuid: {group_guid}")
        else:
            # 如果没有找到原始DWG记录，使用默认值
            attachment_type = 1
            created_by = 'DWG2JPG API'
            group_guid = None
            tag = 'DWG转JPG'
            version = 1
            logger.warning(f"未找到原始DWG文件的记录，使用默认值: {original_dwg_path}")
        
        # 计算相对路径而不是使用绝对路径
        # 获取DWG_FILE_PREFIX环境变量作为基准路径
        dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
        relative_jpg_path = str(jpg_path)
        
        # 如果设置了DWG_FILE_PREFIX，并且JPG路径以该前缀开头，则移除前缀
        if dwg_file_prefix and relative_jpg_path.startswith(dwg_file_prefix):
            # 移除前缀并确保路径以斜杠开头
            relative_jpg_path = relative_jpg_path[len(dwg_file_prefix):]
            # 确保路径以斜杠开头
            if not relative_jpg_path.startswith('/') and not relative_jpg_path.startswith('\\'):
                relative_jpg_path = '/' + relative_jpg_path
            logger.info(f"已将绝对路径转换为相对路径: {relative_jpg_path}")
        else:
            # 如果无法基于DWG_FILE_PREFIX计算相对路径，但有原始DWG文件的记录，尝试从原始DWG路径推断
            if dwg_record and 'FilePath' in dwg_record:
                original_dwg_relative_path = dwg_record['FilePath']
                # 保留原始DWG文件的目录结构，只替换文件名
                dwg_dir_in_db = os.path.dirname(original_dwg_relative_path)
                if dwg_dir_in_db:
                    relative_jpg_path = os.path.join(dwg_dir_in_db, jpg_filename)
                    # 确保路径以斜杠开头
                    if not relative_jpg_path.startswith('/') and not relative_jpg_path.startswith('\\'):
                        relative_jpg_path = '/' + relative_jpg_path
                    logger.info(f"基于原始DWG路径推断的相对路径: {relative_jpg_path}")
                else:
                    # 回退到使用文件名部分
                    logger.warning(f"无法从原始DWG路径推断目录结构，使用文件名部分")
                    relative_jpg_path = '/' + jpg_filename
            else:
                # 如果没有原始DWG记录，记录警告并使用原始路径的文件名部分
                logger.warning(f"无法基于DWG_FILE_PREFIX({dwg_file_prefix})计算相对路径且无原始DWG记录，使用文件名部分")
                relative_jpg_path = '/' + jpg_filename
            
            # 统一路径分隔符为斜杠
            relative_jpg_path = relative_jpg_path.replace('\\', '/')
        
        # 插入JPG文件到C_Attachment表
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
                istojpg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            order_id,  # RefId: 订单ID
            attachment_type,  # AttachmentType: 附件类型，与原始DWG相同或使用默认值
            jpg_filename,  # FileName: JPG文件名
            relative_jpg_path,  # FilePath: JPG文件相对路径
            created_by,  # CreatedBy: 创建者
            current_time,  # CreatedDateTime: 创建时间
            group_guid,  # GroupGuid: 分组GUID，与原始DWG相同
            tag,  # Tag: 标签
            version,  # Version: 版本号
            1  # istojpg: 暂时保持为1，后续会更新为istojpg字段
        )
        
        affected_rows = db.execute_query(insert_query, params)
        logger.info(f"已将JPG文件插入到C_Attachment表，文件名: {jpg_filename}，受影响行数: {affected_rows}")
        return True
        
    except Exception as db_error:
        logger.error(f"将JPG文件插入到C_Attachment表失败: {str(db_error)}")
        return False

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

def update_conversion_status(order_id, file_path, status, error_message=""):
    """更新转换状态，更新C_Attachment表中的istojpg字段表示转换状态（注意：istojpg是历史遗留字段名，实际存储的是JPG转换状态）"""
    try:
        logger.info(f"更新订单ID: {order_id} 的转换状态为: {status}")
        
        # 标准化文件路径，确保与数据库中的路径格式一致
        normalized_file_path = file_path.replace('/', '\\')
        
        if status == "失败":
            update_query = """
                UPDATE C_Attachment
                SET istojpg = -1
                WHERE RefId = ? AND FilePath = ?
            """
            affected_rows = db.execute_query(update_query, (order_id, normalized_file_path))
            logger.info(f"已更新C_Attachment表，标记文件处理失败，受影响行数: {affected_rows}")
        elif status == "成功":
            update_query = """
                UPDATE C_Attachment
                SET istojpg = 1
                WHERE RefId = ? AND FilePath = ?
            """
            affected_rows = db.execute_query(update_query, (order_id, normalized_file_path))
            logger.info(f"已更新C_Attachment表，标记文件处理成功，受影响行数: {affected_rows}")
        
        # 如果没有找到记录，尝试使用LIKE操作符进行模糊匹配
        if affected_rows == 0:
            logger.warning(f"未找到订单ID: {order_id} 的文件记录: {normalized_file_path}")
            # 尝试使用LIKE操作符进行模糊匹配
            like_query = """
                UPDATE C_Attachment
                SET istojpg = ?
                WHERE RefId = ? AND FilePath LIKE ?
            """
            istojpg_value = -1 if status == "失败" else 1
            like_affected_rows = db.execute_query(like_query, 
                (istojpg_value, order_id, f'%{os.path.basename(normalized_file_path)}%'))
            if like_affected_rows > 0:
                logger.info(f"通过文件名模糊匹配找到了记录，已更新 {like_affected_rows} 条记录")
    except Exception as db_error:
        logger.error(f"更新转换状态失败: {str(db_error)}")
        # 记录详细的错误信息，包括参数值
        logger.error(f"失败参数: order_id={order_id}, file_path={file_path}, status={status}")