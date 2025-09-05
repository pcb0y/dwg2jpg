#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging

import ezdxf
# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



# 然后测试我们的转换函数
def test_converter_functions():
    """
    测试DWG2PDF Converter包的函数
    """
    try:
        # 直接使用temp\output目录下已有的DXF文件
        test_dxf_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp', 'output')
        
        # 检查目录是否存在
        if not os.path.exists(test_dxf_dir):
            logger.error(f"DXF文件目录不存在: {test_dxf_dir}")
            return
        
        # 查找测试用的DXF文件 - 优先使用"组合-2.dxf"
        test_dxf_files = [f for f in os.listdir(test_dxf_dir) if f.lower().endswith('.dxf')]
        
        if not test_dxf_files:
            logger.error(f"在{test_dxf_dir}目录下未找到任何DXF文件")
            return
        
        # 优先选择"组合-2.dxf"，如果不存在则使用第一个找到的DXF文件
        test_dxf_filename = '组合-2.dxf' if '组合-2.dxf' in test_dxf_files else test_dxf_files[0]
        test_dxf_path = os.path.join(test_dxf_dir, test_dxf_filename)
        
        logger.info(f"使用已有的测试DXF文件: {test_dxf_path}")
        logger.info(f"DXF目录内容: {test_dxf_files}")
        
        # 准备输出文件路径 - 使用temp\output目录
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp', 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"创建输出目录: {output_dir}")
        
        file_basename = os.path.splitext(os.path.basename(test_dxf_path))[0]
        pdf_output_path = os.path.join(output_dir, f'{file_basename}_output.pdf')
        jpg_output_path = os.path.join(output_dir, f'{file_basename}_output.jpg')
        
        # 导入我们的DWG2PDF Converter包
        from dwg2pdf_converter import convert_dxf_to_jpg
        
        # 测试DXF到JPG转换
        try:
            logger.info(f"开始测试DXF到JPG转换: {test_dxf_path} -> {jpg_output_path}")
            doc = ezdxf.readfile(test_dxf_path)
            success = convert_dxf_to_jpg(doc, jpg_output_path)
            if success and os.path.exists(jpg_output_path):
                logger.info(f"✓ DXF到JPG转换测试成功，输出文件: {jpg_output_path}")
            else:
                logger.error(f"✗ DXF到JPG转换测试失败")
        except Exception as e:
            logger.error(f"✗ DXF到JPG转换测试异常: {str(e)}")
            
    except Exception as e:
        logger.error(f"创建测试文件或执行转换时出错: {str(e)}")

def test_dwg_to_dxf_conversion():
    """
    测试DWG到DXF转换函数
    """
    try:
        from dwg2pdf_converter import convert_dwg_to_dxf
        
        logger.info("开始测试DWG到DXF转换")
        # 注意：convert_dwg_to_dxf函数实际上不使用传入的参数，而是直接使用temp目录下的固定文件
        success = convert_dwg_to_dxf("dummy_path.dwg")
        
        if success:
            logger.info("✓ DWG到DXF转换测试成功")
        else:
            logger.error("✗ DWG到DXF转换测试失败")
    except Exception as e:
        logger.error(f"✗ DWG到DXF转换测试异常: {str(e)}")


def run_tests():
    """
    运行所有测试
    """
    logger.info("=== 开始测试DWG2PDF Converter包 ===")
    
    # 1. 测试DWG到DXF转换函数
    logger.info("\n--- 测试1: DWG到DXF转换功能测试 ---")
    test_dwg_to_dxf_conversion()
    
    # 2. 测试DXF相关的转换函数
    logger.info("\n--- 测试2: DXF转换函数功能测试 ---")
    test_converter_functions()
    
    logger.info("\n=== 测试结束 ===")

if __name__ == '__main__':
    # 运行所有测试
    run_tests()