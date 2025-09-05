import os
import logging
from dotenv import load_dotenv
from main import SQLDatabase, init_database, db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-fix-test")

# 加载.env文件中的环境变量
load_dotenv()

def test_db_fixes():
    """测试修复后的数据库功能"""
    logger.info("=== 开始测试数据库修复 ===")
    
    # 测试1: 验证SQLDatabase类是否有select_query方法
    logger.info("测试1: 验证SQLDatabase类是否有select_query方法")
    has_select_query = hasattr(SQLDatabase, 'select_query')
    if has_select_query:
        logger.info("✓ 通过: SQLDatabase类已包含select_query方法")
    else:
        logger.error("✗ 失败: SQLDatabase类中找不到select_query方法")
    
    # 测试2: 直接调用init_database函数创建表
    logger.info("测试2: 直接调用init_database函数创建conversion_history表")
    try:
        init_database()
        logger.info("✓ 通过: init_database函数调用成功")
    except Exception as e:
        logger.error(f"✗ 失败: 调用init_database函数时出错: {str(e)}")
    
    # 测试3: 尝试插入一条测试记录
    logger.info("测试3: 尝试插入一条测试记录到conversion_history表")
    try:
        test_query = """
            INSERT INTO conversion_history (file_name, original_path, pdf_path, status)
            VALUES (?, ?, ?, ?)
        """
        result = db.execute_query(test_query, ("test.dwg", "C:\\test\\test.dwg", "C:\\test\\test.pdf", "测试"))
        logger.info(f"✓ 通过: 成功插入测试记录，受影响行数: {result}")
    except Exception as e:
        logger.error(f"✗ 失败: 插入测试记录时出错: {str(e)}")
    
    # 测试4: 查询conversion_history表
    logger.info("测试4: 查询conversion_history表中的记录")
    try:
        select_query = "SELECT TOP 1 * FROM conversion_history ORDER BY conversion_time DESC"
        results = db.execute_query(select_query)
        if results:
            logger.info(f"✓ 通过: 查询成功，找到 {len(results)} 条记录")
            logger.info(f"测试记录: {results[0]['id']}, {results[0]['file_name']}, {results[0]['status']}")
        else:
            logger.warning("! 警告: 查询成功，但conversion_history表中暂无记录")
    except Exception as e:
        logger.error(f"✗ 失败: 查询conversion_history表时出错: {str(e)}")
    
    logger.info("=== 数据库修复测试完成 ===")

def main():
    """主函数"""
    # 创建一个新的数据库连接用于测试
    test_db = SQLDatabase()
    
    try:
        # 测试连接
        logger.info("正在连接到数据库...")
        test_db.connect()
        logger.info("数据库连接成功")
        
        # 执行修复测试
        test_db_fixes()
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
    finally:
        # 关闭连接
        if hasattr(test_db, 'disconnect'):
            test_db.disconnect()
            logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()