import logging
from main import SQLDatabase, db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dwg2pdf-check")


# 获取C_Attachment表的结构信息
def get_attachment_table_structure():
    """获取C_Attachment表的结构信息"""
    try:
        logger.info("开始获取C_Attachment表的结构信息")
        
        # 初始化数据库连接
        if not db.conn:
            db.connect()
            logger.info("数据库连接成功")
        
        # 查询表结构信息
        structure_query = """
            SELECT 
                c.name AS ColumnName,
                t.name AS DataType,
                c.max_length,
                c.is_nullable,
                c.is_identity
            FROM 
                sys.columns c
            JOIN 
                sys.types t ON c.user_type_id = t.user_type_id
            WHERE 
                OBJECT_NAME(c.object_id) = 'C_Attachment'
            ORDER BY 
                c.column_id
        """
        
        results = db.execute_query(structure_query)
        
        if results:
            logger.info(f"C_Attachment表的结构信息 (共 {len(results)} 个字段):")
            for field in results:
                logger.info(f"- {field.get('ColumnName')}: {field.get('DataType')}, max_length: {field.get('max_length')}, nullable: {field.get('is_nullable')}")
        else:
            logger.warning("未获取到C_Attachment表的结构信息")
            
        # 查询表中的一些示例数据，以了解数据格式
        sample_query = """
            SELECT TOP 10 * 
            FROM C_Attachment 
            WHERE FilePath LIKE '%.dwg' OR FilePath LIKE '%.pdf'
            ORDER BY id DESC
        """
        
        sample_results = db.execute_query(sample_query)
        
        if sample_results and len(sample_results) > 0:
            logger.info(f"C_Attachment表的示例数据 (前 {min(5, len(sample_results))} 条):")
            # 打印第一条记录的所有字段名，以了解字段格式
            if len(sample_results) > 0:
                first_record = sample_results[0]
                logger.info(f"示例记录字段名: {list(first_record.keys())}")
                # 打印前3条记录的部分关键字段
                for i, record in enumerate(sample_results[:3]):
                    logger.info(f"记录 {i+1}:")
                    logger.info(f"  RefId: {record.get('RefId')}")
                    logger.info(f"  FileName: {record.get('FileName')}")
                    logger.info(f"  FilePath: {record.get('FilePath')}")
                    logger.info(f"  istopdf: {record.get('istopdf')}")
        else:
            logger.warning("未获取到C_Attachment表的示例数据")
            
    except Exception as e:
        logger.error(f"获取表结构过程中发生错误: {str(e)}")
    finally:
        # 断开数据库连接
        if db.conn:
            db.disconnect()


if __name__ == "__main__":
    get_attachment_table_structure()