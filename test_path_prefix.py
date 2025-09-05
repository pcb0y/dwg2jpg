import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 加载.env文件
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dwg2pdf-path-test')

# 测试函数：验证路径前缀拼接逻辑
def test_path_prefix():
    """测试路径前缀拼接逻辑"""
    # 从环境变量中获取DWG文件路径前缀
    dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
    logger.info(f"从环境变量获取的DWG文件路径前缀: {dwg_file_prefix}")
    
    # 测试不同类型的路径
    test_paths = [
        # 以\开头的网络路径
        "\\server\share\path\file.dwg",
        # 带驱动器字母的绝对路径
        "C:\\path\\file.dwg",
        # 相对路径
        "path\\file.dwg",
        # 以\开头的相对路径（可能是从根目录开始的路径）
        "\\path\\file.dwg",
        # 简单文件名
        "file.dwg"
    ]
    
    results = []
    
    for dwg_path in test_paths:
        # 复制convert_dwg_from_database函数中的路径拼接逻辑
        if dwg_path.startswith('\\') or (len(dwg_path) >= 2 and dwg_path[1] == ':'):
            full_dwg_path = dwg_path
        else:
            # 如果路径前缀存在，并且路径不以\开头，则添加\
            if dwg_file_prefix and not dwg_path.startswith('\\'):
                full_dwg_path = dwg_file_prefix + '\\' + dwg_path
            else:
                full_dwg_path = os.path.join(dwg_file_prefix, dwg_path.lstrip('\\'))
        
        results.append({
            'original_path': dwg_path,
            'full_path': full_dwg_path
        })
        
        logger.info(f"原始路径: {dwg_path} -> 完整路径: {full_dwg_path}")
    
    return results


def main():
    """主函数"""
    logger.info("==== 开始测试DWG文件路径前缀拼接功能 ====")
    
    # 运行测试
    test_results = test_path_prefix()
    
    logger.info("\n测试结果总结:")
    for result in test_results:
        logger.info(f"  原始路径: {result['original_path']}")
        logger.info(f"  完整路径: {result['full_path']}")
        logger.info("  " + "-" * 50)
    
    logger.info("==== 测试完成 ====")
    return 0


if __name__ == "__main__":
    sys.exit(main())