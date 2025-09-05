#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
from dwg2pdf_converter.converter import convert_dwg_to_dxf

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_convert_with_paths():
    """测试convert_dwg_to_dxf函数是否能正确处理输入和输出路径"""
    try:
        # 获取当前工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置测试DWG文件路径 - 使用temp目录下的'组合-2.dwg'
        dwg_file = os.path.join(current_dir, 'temp', '组合-2.dwg')
        
        # 检查测试文件是否存在
        if not os.path.exists(dwg_file):
            logger.error(f"测试DWG文件不存在: {dwg_file}")
            return False
        
        logger.info(f"找到测试DWG文件: {dwg_file}")
        
        # 测试场景1: 只提供输入路径，使用默认输出路径
        logger.info("\n=== 测试场景1: 只提供输入路径 ===")
        result1 = convert_dwg_to_dxf(dwg_file)
        logger.info(f"测试场景1结果: {'成功' if result1 else '失败'}")
        
        # 测试场景2: 提供完整的输出路径
        logger.info("\n=== 测试场景2: 提供完整的输出路径 ===")
        output_dir = os.path.join(current_dir, 'temp', 'test_output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        dxf_file = os.path.join(output_dir, 'test_converted.dxf')
        result2 = convert_dwg_to_dxf(dwg_file, dxf_file)
        logger.info(f"测试场景2结果: {'成功' if result2 else '失败'}")
        
        # 检查输出文件是否存在
        if result2 and os.path.exists(dxf_file):
            logger.info(f"成功生成输出文件: {dxf_file}")
        
        # 测试场景3: 输入和输出目录相同的情况
        logger.info("\n=== 测试场景3: 输入和输出目录相同 ===")
        # 尝试使用与DWG相同的目录作为输出目录
        same_dir_dxf = os.path.join(os.path.dirname(dwg_file), 'same_dir_test.dxf')
        result3 = convert_dwg_to_dxf(dwg_file, same_dir_dxf)
        logger.info(f"测试场景3结果: {'成功' if result3 else '失败'}")
        
        # 检查输出文件是否存在
        if result3 and os.path.exists(same_dir_dxf):
            logger.info(f"成功生成输出文件: {same_dir_dxf}")
        
        return result1 and result2 and result3
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== 开始测试convert_dwg_to_dxf路径处理功能 ===")
    success = test_convert_with_paths()
    
    if success:
        logger.info("=== 所有测试场景通过 ===")
        sys.exit(0)
    else:
        logger.error("=== 测试失败 ===")
        sys.exit(1)