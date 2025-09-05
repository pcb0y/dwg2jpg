import os
import logging
import pyodbc
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-connection-test")

# 加载.env文件中的环境变量
load_dotenv()

# 从环境变量中读取数据库连接配置
def get_db_config():
    """从环境变量获取数据库配置"""
    return {
        "server": os.getenv("DB_SERVER", "localhost"),
        "database": os.getenv("DB_DATABASE", "DWG2PDF"),
        "username": os.getenv("DB_USERNAME", "sa"),
        "password": os.getenv("DB_PASSWORD", "your_password"),
        "driver": os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")
    }

def test_db_connection():
    """测试数据库连接是否正常"""
    try:
        # 获取数据库配置
        config = get_db_config()
        
        # 打印当前使用的配置（不打印密码）
        logger.info(f"正在测试数据库连接...")
        logger.info(f"服务器: {config['server']}")
        logger.info(f"数据库: {config['database']}")
        logger.info(f"用户名: {config['username']}")
        logger.info(f"驱动: {config['driver']}")
        
        # 创建连接字符串
        conn_str = f"DRIVER={config['driver']};SERVER={config['server']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
        
        # 尝试建立连接
        logger.info("正在建立连接...")
        conn = pyodbc.connect(conn_str)
        logger.info("数据库连接成功!")
        
        # 测试查询 - 列出所有表
        logger.info("测试执行简单查询...")
        cursor = conn.cursor()
        
        # 查询数据库中的表
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = cursor.fetchall()
        
        if tables:
            logger.info(f"在数据库 '{config['database']}' 中找到以下表:")
            for table in tables:
                logger.info(f"- {table[0]}")
        else:
            logger.warning(f"在数据库 '{config['database']}' 中未找到任何表")
        
        # 检查是否存在转换历史表
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'conversion_history' AND TABLE_TYPE = 'BASE TABLE'")
        has_history_table = cursor.fetchone()[0] > 0
        
        if has_history_table:
            logger.info("找到 'conversion_history' 表")
            # 查询表结构
            cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'conversion_history'")
            columns = cursor.fetchall()
            logger.info("表结构:")
            for column in columns:
                logger.info(f"- {column[0]} ({column[1]})")
            
            # 查询转换历史记录
            cursor.execute("SELECT TOP 5 * FROM conversion_history ORDER BY conversion_time DESC")
            records = cursor.fetchall()
            if records:
                logger.info(f"找到 {len(records)} 条转换历史记录的示例")
                # 打印列名
                column_names = [column[0] for column in cursor.description]
                logger.info(f"列: {', '.join(column_names)}")
                # 打印每条记录的前几个字段
                for i, record in enumerate(records):
                    logger.info(f"记录 {i+1}: {record[0]}, {record[1]}, {record[4]}, {record[5]}")
            else:
                logger.info("'conversion_history' 表中暂无记录")
        else:
            logger.warning("未找到 'conversion_history' 表")
        
        # 检查代码中引用的其他表
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'c_order' AND TABLE_TYPE = 'BASE TABLE'")
        has_c_order = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'C_Attachment' AND TABLE_TYPE = 'BASE TABLE'")
        has_c_attachment = cursor.fetchone()[0] > 0
        
        if has_c_order:
            logger.info("找到 'c_order' 表")
        else:
            logger.warning("未找到 'c_order' 表")
        
        if has_c_attachment:
            logger.info("找到 'C_Attachment' 表")
        else:
            logger.warning("未找到 'C_Attachment' 表")
        
        # 关闭连接
        cursor.close()
        conn.close()
        logger.info("数据库连接已关闭")
        
        return True
        
    except pyodbc.Error as e:
        logger.error(f"数据库连接失败: {str(e)}")
        # 更详细地输出错误信息
        if isinstance(e, pyodbc.OperationalError):
            logger.error("可能的原因: 服务器地址错误、数据库不存在、SQL Server服务未启动")
        elif isinstance(e, pyodbc.ProgrammingError):
            logger.error("可能的原因: 用户名或密码错误、权限不足")
        else:
            logger.error(f"ODBC错误代码: {e.args[0]}")
            if len(e.args) > 1:
                logger.error(f"ODBC错误信息: {e.args[1]}")
        return False
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        return False

def test_main_code_compatibility():
    """测试main.py中发现的一些潜在问题"""
    logger.info("检查main.py中发现的潜在问题...")
    
    # 1. 检查init_database函数中的SQL
    logger.info("问题1: init_database函数中的SQL查询似乎不是创建表的语句，而是一个SELECT语句")
    
    # 2. 检查是否有select_query方法
    logger.info("问题2: 在代码中发现调用了db.select_query方法，但SQLDatabase类中只有execute_query方法")
    
    # 3. 检查数据库操作的一致性
    logger.info("问题3: 代码中有些地方使用了conversion_history表，有些地方使用了c_order和C_Attachment表的JOIN查询")
    
    logger.info("建议修复这些问题以确保系统正常运行")

if __name__ == "__main__":
    logger.info("=== 开始数据库连接测试 ===")
    
    # 运行数据库连接测试
    connection_success = test_db_connection()
    
    # 检查main.py中的潜在问题
    test_main_code_compatibility()
    
    logger.info("=== 数据库连接测试完成 ===")
    
    if connection_success:
        logger.info("总体结论: 数据库连接测试成功，但发现了一些代码逻辑问题需要修复")
    else:
        logger.error("总体结论: 数据库连接测试失败，请检查配置和网络连接")