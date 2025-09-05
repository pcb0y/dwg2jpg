#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF to JPG Converter

将DXF文件转换为JPG图像文件的工具。
使用ezdxf库读取DXF文件，使用matplotlib生成图像。
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import ezdxf
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import LayoutProperties


# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_argument_parser():
    """
    设置命令行参数解析器
    """
    parser = argparse.ArgumentParser(description='将DXF文件转换为JPG图像')
    parser.add_argument('input', help='输入DXF文件路径')
    parser.add_argument('-o', '--output', help='输出JPG文件路径 (默认: 与输入文件同名但扩展名为.jpg)')
    parser.add_argument('-s', '--size', type=int, default=1600, help='输出图像的宽度 (像素, 默认: 1600)')
    parser.add_argument('-b', '--bg', default='white', help='背景颜色 (默认: white)')
    parser.add_argument('-c', '--color', default='black', help='线条颜色 (默认: black)')
    parser.add_argument('-d', '--dpi', type=int, default=300, help='输出图像的DPI (默认: 300)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    return parser


def read_dxf(filepath):
    """
    读取DXF文件
    
    Args:
        filepath: DXF文件路径
        
    Returns:
        ezdxf.drawing.Drawing: DXF文档对象
    """
    try:
        logger.info(f"正在读取DXF文件: {filepath}")
        doc = ezdxf.readfile(filepath)
        return doc
    except IOError as e:
        logger.error(f"无法打开DXF文件: {filepath}")
        logger.error(f"错误: {str(e)}")
        sys.exit(1)
    except ezdxf.DXFStructureError as e:
        logger.error(f"无效的DXF文件或不支持的DXF版本: {filepath}")
        logger.error(f"错误: {str(e)}")
        sys.exit(2)


def convert_dxf_to_jpg(doc, output_path, size=1600, bg_color='white', line_color='black', dpi=300):
    """
    将DXF文档转换为JPG图像
    
    Args:
        doc: ezdxf.drawing.Drawing对象
        output_path: 输出JPG文件路径
        size: 输出图像的宽度 (像素)
        bg_color: 背景颜色
        line_color: 线条颜色
        dpi: 输出图像的DPI
        
    Returns:
        bool: 转换是否成功
    """
    try:
        logger.info(f"正在转换DXF为JPG: {output_path}")
        
        # 创建matplotlib图形
        fig = plt.figure(figsize=(size/dpi, size/dpi), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_facecolor(bg_color)
        
        # 设置渲染上下文
        ctx = RenderContext(doc)
        ctx.set_current_layout(doc.modelspace())
        
        # 获取布局属性并设置颜色
        msp_properties = LayoutProperties.from_layout(doc.modelspace())
        # 将颜色名称转换为十六进制格式
        # 背景色默认为白色 #FFFFFF，前景色默认为黑色 #000000
        bg_hex = "#FFFFFF" if bg_color == "white" else "#000000" if bg_color == "black" else bg_color
        fg_hex = "#000000" if line_color == "black" else "#FFFFFF" if line_color == "white" else line_color
        
        # 如果颜色已经是十六进制格式但没有 # 前缀，添加前缀
        if not bg_hex.startswith("#") and len(bg_hex) == 6:
            bg_hex = "#" + bg_hex
        if not fg_hex.startswith("#") and len(fg_hex) == 6:
            fg_hex = "#" + fg_hex
            
        # 设置前景色（线条颜色）和背景色
        msp_properties.set_colors(bg_hex, fg=fg_hex)
        
        # 创建后端和前端
        backend = MatplotlibBackend(ax)
        frontend = Frontend(ctx, backend)
        
        # 渲染DXF实体
        frontend.draw_layout(doc.modelspace(), finalize=True, layout_properties=msp_properties)
        
        # 调整视图以适应所有实体
        ax.autoscale(tight=True)
        ax.set_aspect('equal')
        
        # 保存为JPG
        canvas = FigureCanvas(fig)
        fig.savefig(output_path, format='jpg', dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"转换完成: {output_path}")
        return True
    except Exception as e:
        logger.error(f"转换过程中出错")
        logger.error(f"错误: {str(e)}")
        return False


def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}")
        sys.exit(1)
    
    # 设置输出文件路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.jpg')
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取DXF文件
    doc = read_dxf(input_path)
    
    # 转换为JPG
    success = convert_dxf_to_jpg(
        doc, 
        str(output_path), 
        size=args.size, 
        bg_color=args.bg, 
        line_color=args.color,
        dpi=args.dpi
    )
    
    if success:
        logger.info(f"转换成功: {input_path} -> {output_path}")
        return 0
    else:
        logger.error(f"转换失败: {input_path}")
        return 3


if __name__ == "__main__":
    sys.exit(main())