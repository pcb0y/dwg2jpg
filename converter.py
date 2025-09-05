
from pathlib import Path
from logger_config import logger
# 注意：dwg2jpg.converter模块没有提供convert_dwg_to_pdf函数，提供了convert_dwg_to_jpg函数
from dwg2jpg.converter import convert_dwg_to_jpg



def converter_dwg_to_jpg(dwg_path, jpg_path, size=1600, bg_color='white', line_color='black', dpi=300):
    """使用dwg2jpg库将DWG文件转换为JPG图像"""
    logger.info(f"使用dwg2jpg库进行DWG到JPG转换: {dwg_path} -> {jpg_path}")
    
    try:
        # 调用dwg2jpg库的转换函数
        success = convert_dwg_to_jpg(dwg_path, jpg_path, size, bg_color, line_color, dpi)
        
        # 验证转换结果
        jpg_file = Path(jpg_path)
        if not jpg_file.exists():
            raise FileNotFoundError(f"JPG文件未创建: {jpg_path}")
        
        # 获取文件大小作为额外验证
        jpg_size = jpg_file.stat().st_size
        if jpg_size == 0:
            raise ValueError(f"创建的JPG文件为空: {jpg_size} 字节")
        
        logger.info(f"dwg2jpg库转换成功，JPG文件大小: {jpg_size} 字节")
        return True
    except Exception as e:
        logger.error(f"dwg2jpg库转换失败: {str(e)}")
        return False