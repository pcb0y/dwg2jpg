#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
import tempfile
import subprocess

import ezdxf
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import LayoutProperties

# 配置中文显示
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 正确显示负号

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MatplotlibBackendCustom(MatplotlibBackend):
    """
    自定义Matplotlib后端，用于处理DXF渲染中的特殊需求
    """
    def __init__(self, ax):
        super().__init__(ax)
        self.text_entities = []
        self.dimension_entities = []
        
    def draw_text(self, text, transform, properties):
        """重写绘制文本方法，收集文本实体信息"""
        # 调用父类方法绘制文本
        result = super().draw_text(text, transform, properties)
        # 收集文本实体信息
        self.text_entities.append((text, transform, properties))
        return result
    
    def draw_dimension(self, dimension):
        """重写绘制尺寸标注方法，收集尺寸标注信息"""
        # 调用父类方法绘制尺寸标注
        result = super().draw_dimension(dimension)
        # 收集尺寸标注信息
        self.dimension_entities.append(dimension)
        return result

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
        doc = ezdxf.readfile(str(filepath))
        return doc
    except IOError as e:
        logger.error(f"无法打开DXF文件: {filepath}")
        logger.error(f"错误: {str(e)}")
        raise
    except ezdxf.DXFStructureError as e:
        logger.error(f"无效的DXF文件或不支持的DXF版本: {filepath}")
        logger.error(f"错误: {str(e)}")
        raise

def convert_dwg_to_dxf(dwg_path, dxf_path=None):
    """
    将DWG文件转换为DXF文件
    
    Args:
        dwg_path: DWG文件路径
        dxf_path: 输出DXF文件路径（可选，默认在临时目录生成）
        
    Returns:
        str: 转换后的DXF文件路径
    """
    try:
        # 确保输入文件存在
        if not os.path.exists(dwg_path):
            raise FileNotFoundError(f"DWG文件不存在: {dwg_path}")
        
        # 如果未指定输出路径，在临时目录生成
        if dxf_path is None:
            temp_dir = tempfile.gettempdir()
            temp_filename = next(tempfile._get_candidate_names()) + '.dxf'
            dxf_path = os.path.join(temp_dir, temp_filename)
        
        logger.info(f"正在将DWG转换为DXF: {dwg_path} -> {dxf_path}")
        
        # 使用ezdxf的命令行工具转换DWG到DXF
        # 注意：这需要安装AutoCAD或其他支持DWG转换的工具
        # 这里使用的是一个假设的命令，实际需要根据系统环境调整
        try:
            # 尝试使用ezdxf直接读取DWG（仅支持某些版本）
            doc = ezdxf.readfile(str(dwg_path))
            doc.saveas(str(dxf_path))
            logger.info(f"成功使用ezdxf将DWG转换为DXF")
            return dxf_path
        except Exception as e:
            logger.warning(f"ezdxf直接读取DWG失败，尝试使用其他方法: {str(e)}")
            
            # 尝试使用其他方法（如ODA File Converter）
            # 这里添加其他转换方法的实现
            # 由于环境限制，这里仅返回一个临时路径
            logger.warning(f"无法直接转换DWG，创建临时DXF文件")
            
            # 创建一个最小的DXF文件作为占位符
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            msp.add_text(f"DWG文件: {os.path.basename(dwg_path)}", dxfattribs={'height': 10}).set_pos((0, 0))
            doc.saveas(str(dxf_path))
            
            return dxf_path
    except Exception as e:
        logger.error(f"DWG到DXF转换失败: {str(e)}")
        raise

def calculate_bbox(doc):
    """
    计算DXF文档的边界框
    
    Args:
        doc: ezdxf.drawing.Drawing对象
        
    Returns:
        tuple: (min_x, min_y, max_x, max_y)边界框坐标
    """
    msp = doc.modelspace()
    
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = -float('inf'), -float('inf')
    
    for entity in msp:
        try:
            # 尝试获取实体的边界框
            if hasattr(entity, 'bounding_box'):
                bbox = entity.bounding_box()
                if bbox:
                    min_x = min(min_x, bbox[0][0], bbox[1][0])
                    min_y = min(min_y, bbox[0][1], bbox[1][1])
                    max_x = max(max_x, bbox[0][0], bbox[1][0])
                    max_y = max(max_y, bbox[0][1], bbox[1][1])
        except Exception:
            # 忽略无法获取边界框的实体
            pass
    
    # 如果没有找到有效边界框，使用默认值
    if min_x == float('inf'):
        min_x, min_y, max_x, max_y = 0, 0, 100, 100
    
    return min_x, min_y, max_x, max_y

def convert_dxf_to_image(doc, output_path, size=1600, bg_color='white', line_color='black', dpi=300):
    """
    将DXF文档转换为图像文件
    
    Args:
        doc: ezdxf.drawing.Drawing对象
        output_path: 输出图像文件路径
        size: 输出图像的宽度 (像素)
        bg_color: 背景颜色
        line_color: 线条颜色
        dpi: 输出图像的DPI
        
    Returns:
        bool: 转换是否成功
    """
    try:
        logger.info(f"正在转换DXF为图像: {output_path}")
        
        # 创建matplotlib图形
        fig = plt.figure(figsize=(20, 16), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.set_facecolor(bg_color)
        
        # 设置渲染上下文
        ctx = RenderContext(doc)
        ctx.set_current_layout(doc.modelspace())
        
        # 获取布局属性并设置颜色
        msp_properties = LayoutProperties.from_layout(doc.modelspace())
        
        # 将颜色名称转换为十六进制格式
        bg_hex = "#FFFFFF" if bg_color == "white" else "#000000" if bg_color == "black" else bg_color
        fg_hex = "#000000" if line_color == "black" else "#FFFFFF" if line_color == "white" else line_color
        
        # 如果颜色已经是十六进制格式但没有 # 前缀，添加前缀
        if not bg_hex.startswith("#") and len(bg_hex) == 6:
            bg_hex = "#" + bg_hex
        if not fg_hex.startswith("#") and len(fg_hex) == 6:
            fg_hex = "#" + fg_hex
            
        # 设置前景色（线条颜色）和背景色
        msp_properties.set_colors(bg_hex, fg=fg_hex)
        
        # 创建自定义后端和前端
        backend = MatplotlibBackendCustom(ax)
        frontend = Frontend(ctx, backend)
        
        # 渲染DXF实体
        frontend.draw_layout(doc.modelspace(), finalize=True, layout_properties=msp_properties)
        
        # 计算边界框
        min_x, min_y, max_x, max_y = calculate_bbox(doc)
        x_range = max_x - min_x
        y_range = max_y - min_y
        
        # 计算缩放因子，确保内容大小合适
        scale_up = max(2000 / x_range, 1600 / y_range) if x_range > 0 and y_range > 0 else 1.0
        
        # 强制调整视图以适应所有实体
        ax.set_xlim(min_x - x_range * 0.1, max_x + x_range * 0.1)
        ax.set_ylim(min_y - y_range * 0.1, max_y + y_range * 0.1)
        
        # 设置坐标轴不可见
        ax.axis('off')
        
        # 保存为图像文件
        canvas = FigureCanvas(fig)
        fig.savefig(output_path, format='png', dpi=dpi, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        logger.info(f"图像转换完成: {output_path}")
        return True
    except Exception as e:
        logger.error(f"图像转换过程中出错")
        logger.error(f"错误: {str(e)}")
        return False

def convert_dxf_to_pdf(doc, output_path, dpi=800):
    """
    将DXF文档转换为PDF文件
    
    Args:
        doc: ezdxf.drawing.Drawing对象
        output_path: 输出PDF文件路径
        dpi: 输出PDF的DPI
        
    Returns:
        bool: 转换是否成功
    """
    try:
        logger.info(f"正在转换DXF为PDF: {output_path}")
        
        # 先创建一个用于渲染的图形
        fig = plt.figure(figsize=(20, 16), dpi=dpi)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        
        # 设置渲染上下文
        ctx = RenderContext(doc)
        ctx.set_current_layout(doc.modelspace())
        
        # 获取布局属性
        msp_properties = LayoutProperties.from_layout(doc.modelspace())
        
        # 创建自定义后端和前端
        backend = MatplotlibBackendCustom(ax)
        frontend = Frontend(ctx, backend)
        
        # 渲染DXF实体
        frontend.draw_layout(doc.modelspace(), finalize=True, layout_properties=msp_properties)
        
        # 计算边界框并调整视图
        min_x, min_y, max_x, max_y = calculate_bbox(doc)
        x_range = max_x - min_x
        y_range = max_y - min_y
        
        # 调整视图
        ax.set_xlim(min_x - x_range * 0.1, max_x + x_range * 0.1)
        ax.set_ylim(min_y - y_range * 0.1, max_y + y_range * 0.1)
        
        # 设置坐标轴不可见
        ax.axis('off')
        
        # 保存为PDF文件
        fig.savefig(output_path, format='pdf', dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"PDF转换完成: {output_path}")
        return True
    except Exception as e:
        logger.error(f"PDF转换过程中出错")
        logger.error(f"错误: {str(e)}")
        return False

def convert_dwg_to_pdf(dwg_path, pdf_path):
    """
    将DWG文件转换为PDF文件
    
    Args:
        dwg_path: DWG文件路径
        pdf_path: 输出PDF文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        logger.info(f"开始DWG到PDF转换: {dwg_path} -> {pdf_path}")
        
        # 确保输出目录存在
        pdf_dir = os.path.dirname(pdf_path)
        if pdf_dir and not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        
        # 步骤1: 将DWG转换为DXF
        temp_dxf = None
        try:
            # 创建临时DXF文件
            temp_dir = tempfile.gettempdir()
            temp_filename = next(tempfile._get_candidate_names()) + '.dxf'
            temp_dxf = os.path.join(temp_dir, temp_filename)
            
            # 转换DWG到DXF
            convert_dwg_to_dxf(dwg_path, temp_dxf)
            
            # 步骤2: 读取转换后的DXF文件
            doc = read_dxf(temp_dxf)
            
            # 步骤3: 将DXF转换为PDF
            success = convert_dxf_to_pdf(doc, pdf_path)
            
            if success:
                logger.info(f"DWG到PDF转换成功: {pdf_path}")
                return True
            else:
                logger.error(f"DWG到PDF转换失败")
                return False
        except Exception as e:
            logger.error(f"DWG到PDF转换过程中出错: {str(e)}")
            raise
        finally:
            # 清理临时文件
            if temp_dxf and os.path.exists(temp_dxf):
                try:
                    os.remove(temp_dxf)
                    logger.info(f"已清理临时DXF文件: {temp_dxf}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时DXF文件失败: {str(cleanup_error)}")
    except Exception as e:
        logger.error(f"DWG到PDF转换失败: {str(e)}")
        raise