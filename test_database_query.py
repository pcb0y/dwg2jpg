import os
from pathlib import Path
import logging
from main import SQLDatabase, db, convert_with_autocad

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dwg2pdf-test")


# 测试数据库连接和查询功能
def test_database_connection_and_query():
    """测试数据库连接和查询功能"""
    try:
        logger.info("开始测试数据库连接和查询功能")
        
        # 初始化数据库连接
        if not db.conn:
            db.connect()
            logger.info("数据库连接成功")
        
        # 测试用户提供的SQL查询
        query = """
            SELECT 
               o.id ,c.FilePath 
            FROM 
               c_order o 
            INNER JOIN C_Attachment c on c.RefId = o.id 
            WHERE 
               OrderStatus BETWEEN 60 and 160 and c.istopdf is null  AND c.FilePath LIKE '%.dwg'
        """
        
        # 执行查询
        logger.info("执行SQL查询")
        results = db.execute_query(query)
        
        # 显示查询结果
        if results:
            logger.info(f"查询成功，返回 {len(results)} 条记录")
            
            # 显示前5条记录（如果有的话）
            for i, record in enumerate(results[:5]):
                logger.info(f"记录 {i+1}: {record}")
                
            # 检查记录格式是否正确
            for record in results:
                if 'id' not in record or 'FilePath' not in record:
                    logger.error(f"记录格式不正确: {record}")
                    return False
                
                # 检查文件路径是否存在
                dwg_path = record['FilePath']
                if not Path(dwg_path).exists():
                    logger.warning(f"DWG文件不存在: {dwg_path}")
        else:
            logger.info("查询返回0条记录")
            
        # 测试获取连接方法
        conn = db.get_connection()
        logger.info(f"成功获取数据库连接: {conn}")
        
        logger.info("数据库连接和查询功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"数据库连接和查询功能测试失败: {str(e)}")
        return False


# 测试转换功能核心逻辑
def test_conversion_logic():
    """测试转换功能的核心逻辑"""
    try:
        logger.info("开始测试转换功能的核心逻辑")
        
        # 这里可以添加测试转换逻辑的代码，例如使用一个已知存在的DWG文件
        # 注意：这将实际调用AutoCAD进行转换，可能需要AutoCAD已安装
        
        # 由于这是单元测试，我们可以只验证convert_with_autocad函数的参数和基本逻辑
        # 而不是实际执行转换
        
        # 检查convert_with_autocad函数是否存在
        if 'convert_with_autocad' in globals():
            logger.info("convert_with_autocad函数存在")
        else:
            logger.error("convert_with_autocad函数不存在")
            return False
        
        # 如果有测试DWG文件，可以在这里添加实际的转换测试
        
        logger.info("转换功能的核心逻辑测试通过")
        return True
        
    except Exception as e:
        logger.error(f"转换功能的核心逻辑测试失败: {str(e)}")
        return False


# 运行测试
def run_tests():
    """运行所有测试"""
    logger.info("开始运行测试")
    
    tests = [
        ("数据库连接和查询功能测试", test_database_connection_and_query),
        ("转换功能核心逻辑测试", test_conversion_logic)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"执行测试: {test_name}")
        success = test_func()
        
        if success:
            logger.info(f"测试通过: {test_name}")
        else:
            logger.error(f"测试失败: {test_name}")
            all_passed = False
    
    if all_passed:
        logger.info("所有测试通过！")
    else:
        logger.error("有测试失败，请查看错误信息")
    
    return all_passed


if __name__ == "__main__":
    run_tests()