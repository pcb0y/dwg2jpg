import os
from pathlib import Path
import logging
from main import SQLDatabase, db, insert_pdf_to_attachment

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dwg2pdf-test")


# 测试将PDF文件插入到C_Attachment表
def test_insert_pdf_to_attachment():
    """测试将PDF文件插入到C_Attachment表的功能"""
    try:
        logger.info("开始测试将PDF文件插入到C_Attachment表的功能")
        
        # 初始化数据库连接
        if not db.conn:
            db.connect()
            logger.info("数据库连接成功")
        
        # 测试参数设置
        # 注意：这些是测试参数，需要根据实际情况修改
        test_order_id = "123"  # 测试订单ID
        test_dwg_path = "\\订单其他附件\\test\\sample.dwg"  # 测试DWG文件路径
        
        # 创建一个测试PDF文件（如果不存在）
        temp_dir = os.path.join(os.getenv("TEMP", "."), "dwg2pdf_test")
        os.makedirs(temp_dir, exist_ok=True)
        
        test_pdf_filename = f"test_order_{test_order_id}.pdf"
        test_pdf_path = os.path.join(temp_dir, test_pdf_filename)
        
        # 创建测试PDF文件内容
        if not os.path.exists(test_pdf_path):
            with open(test_pdf_path, "w", encoding="utf-8") as f:
                f.write("%PDF-1.4\n%测试PDF文件内容\n\ntrailer<</Size 1>>\nstartxref\n0\n%%EOF")
            logger.info(f"已创建测试PDF文件: {test_pdf_path}")
        
        # 调用插入函数
        logger.info(f"调用insert_pdf_to_attachment函数，订单ID: {test_order_id}，PDF路径: {test_pdf_path}")
        result = insert_pdf_to_attachment(test_order_id, test_pdf_path, test_dwg_path)
        
        if result:
            logger.info("测试成功：PDF文件成功插入到C_Attachment表")
            
            # 验证插入是否成功
            verify_insertion(test_order_id, test_pdf_filename)
            
            return True
        else:
            logger.error("测试失败：无法将PDF文件插入到C_Attachment表")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        return False
    finally:
        # 可选：清理测试PDF文件
        # if os.path.exists(test_pdf_path):
        #     os.remove(test_pdf_path)
        #     logger.info(f"已删除测试PDF文件: {test_pdf_path}")
        pass


# 验证插入是否成功
def verify_insertion(order_id, pdf_filename):
    """验证PDF文件是否成功插入到C_Attachment表"""
    try:
        logger.info(f"验证订单ID: {order_id} 的PDF文件 {pdf_filename} 是否成功插入到C_Attachment表")
        
        # 查询C_Attachment表验证插入
        verify_query = """
            SELECT TOP 1 * 
            FROM C_Attachment 
            WHERE RefId = ? AND FileName = ? AND istopdf = 1
            ORDER BY UploadTime DESC
        """
        
        results = db.execute_query(verify_query, (order_id, pdf_filename))
        
        if results and len(results) > 0:
            logger.info(f"验证成功：找到插入的PDF文件记录")
            logger.info(f"插入的记录信息: {results[0]}")
            
            # 打印一些关键字段的值
            record = results[0]
            logger.info(f"RefId: {record.get('RefId')}")
            logger.info(f"FileName: {record.get('FileName')}")
            logger.info(f"FilePath: {record.get('FilePath')}")
            logger.info(f"FileSize: {record.get('FileSize')}")
            logger.info(f"FileExt: {record.get('FileExt')}")
            logger.info(f"FileType: {record.get('FileType')}")
            logger.info(f"UploadTime: {record.get('UploadTime')}")
            logger.info(f"istopdf: {record.get('istopdf')}")
        else:
            logger.warning(f"验证失败：未找到插入的PDF文件记录")
            
    except Exception as e:
        logger.error(f"验证过程中发生错误: {str(e)}")


# 获取C_Attachment表的结构信息
def get_attachment_table_structure():
    """获取C_Attachment表的结构信息，用于调试"""
    try:
        logger.info("获取C_Attachment表的结构信息")
        
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
            
    except Exception as e:
        logger.error(f"获取表结构过程中发生错误: {str(e)}")


# 运行测试
def run_tests():
    """运行所有测试"""
    logger.info("开始运行测试")
    
    # 首先获取表结构信息，这有助于调试
    get_attachment_table_structure()
    
    # 运行插入测试
    insert_test_result = test_insert_pdf_to_attachment()
    
    if insert_test_result:
        logger.info("所有测试通过！")
    else:
        logger.error("测试失败，请查看错误信息")
    
    # 断开数据库连接
    if db.conn:
        db.disconnect()


if __name__ == "__main__":
    run_tests()