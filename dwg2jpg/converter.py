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
    把dwg文件转换为dxf文件
    
    Args:
        dwg_path: DWG文件路径
        dxf_path: 输出DXF文件路径，如果不提供则使用与DWG相同的目录
        
    Returns:
        bool: 转换是否成功
    """
    try:
        # 定义ODA转换器路径 - 根据项目结构，ODA文件夹位于项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        oda_converter_path = os.path.join(project_root, 'ODA', 'ODAFileConverter26.7.0', 'ODAFileConverter.exe')
        
        if not os.path.exists(oda_converter_path):
            logger.error(f"ODA转换工具不存在: {oda_converter_path}")
            return False
        
        logger.info(f"ODA转换工具路径: {oda_converter_path}")
        
        # 检查输入DWG文件是否存在
        if not os.path.exists(dwg_path):
            logger.error(f"输入DWG文件不存在: {dwg_path}")
            return False
        
        logger.info(f"使用DWG文件: {dwg_path}")
        
        # 确定输出目录和文件名
        input_dir = os.path.dirname(dwg_path)
        input_filename = os.path.basename(dwg_path)
        
        # 如果提供了dxf_path，则使用它；否则使用默认的临时目录
        if dxf_path:
            # 确保输出目录存在
            output_dir = os.path.dirname(dxf_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 构建临时输出目录（用于ODA转换）
            temp_output_dir = os.path.dirname(dxf_path)
        else:
            # 默认使用临时目录，而不是与DWG相同的目录，以避免输入输出目录相同
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_output_dir = os.path.join(project_root, 'temp', 'output')
            os.makedirs(temp_output_dir, exist_ok=True)
        
        # 检查输入和输出目录是否相同
        normalized_input_dir = os.path.normpath(input_dir)
        normalized_output_dir = os.path.normpath(temp_output_dir)
        
        if normalized_input_dir == normalized_output_dir:
            # 如果输入和输出目录相同，创建一个唯一的临时目录
            import tempfile
            temp_output_dir = tempfile.mkdtemp(prefix='dxf_convert_')
            logger.warning(f"输入和输出目录不能相同，已创建临时输出目录: {temp_output_dir}")
        
        logger.info(f"输入目录: {input_dir}")
        logger.info(f"输出目录: {temp_output_dir}")
        logger.info(f"输入文件名: {input_filename}")
        
        # 确保输出目录存在
        if not os.path.exists(temp_output_dir):
            os.makedirs(temp_output_dir, exist_ok=True)
        
        # 列出输入目录中的文件
        logger.info(f"输入目录内容: {os.listdir(input_dir)}")
        
        # 构建ODA转换命令 - 修改参数确保输出为DXF格式
        cmd_args = [
            oda_converter_path,
            input_dir,  # 输入目录
            temp_output_dir,  # 输出目录
            'ACAD2018',  # 输出版本
            'DXF',  # 输出格式设置为DXF
            '0',  # 0表示转换所有文件
            input_filename  # 要转换的文件名
        ]
            
        logger.info(f"执行ODA转换命令: {' '.join(cmd_args)}")
        
        # 执行命令
        result = subprocess.run(
            cmd_args,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"ODA转换成功，输出: {result.stdout}")
        logger.info(f"ODA错误输出: {result.stderr}")
            
        # 检查是否有DXF文件生成
        output_files = os.listdir(temp_output_dir)
        logger.info(f"输出目录内容: {output_files}")
        
        # 找到转换后的DXF文件
        base_name = os.path.splitext(input_filename)[0]
        dxf_files = [f for f in output_files if f.lower().startswith(base_name.lower()) and f.lower().endswith('.dxf')]
        
        if dxf_files:
            logger.info(f"找到转换后的DXF文件: {dxf_files}")
            
            # 如果指定了特定的dxf_path，且转换后的文件名与目标文件名不同，则移动文件
            if dxf_path and os.path.basename(dxf_path) not in dxf_files:
                source_dxf = os.path.join(temp_output_dir, dxf_files[0])
                try:
                    # 首先尝试使用os.rename，这在同一磁盘上效率更高
                    os.rename(source_dxf, dxf_path)
                except OSError:
                    # 如果跨磁盘，则使用shutil.move
                    import shutil
                    shutil.move(source_dxf, dxf_path)
                logger.info(f"已将文件移动到: {dxf_path}")
            
            return True
        else:
            logger.error(f"未找到转换后的DXF文件")
            return False
                
    except Exception as e:
        logger.error(f"创建测试文件或执行ODA转换时出错: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"测试ODA转换器时出错: {str(e)}")
        return False

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




def convert_dwg_to_jpg(dwg_path, jpg_path, size=3200, bg_color='white', line_color='black', dpi=600):
    """
    将DWG文件直接转换为JPG图像
    
    Args:
        dwg_path: DWG文件路径
        jpg_path: 输出JPG文件路径
        size: 输出图像的宽度 (像素)
        bg_color: 背景颜色
        line_color: 线条颜色
        dpi: 输出图像的DPI
        
    Returns:
        bool: 转换是否成功
    """
    try:
        logger.info(f"开始DWG到JPG的完整转换: {dwg_path} -> {jpg_path}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(jpg_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 生成临时DXF文件路径
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='dwg2jpg_')
        base_name = os.path.splitext(os.path.basename(dwg_path))[0]
        temp_dxf_path = os.path.join(temp_dir, f"{base_name}.dxf")
        
        logger.info(f"创建临时DXF文件: {temp_dxf_path}")
        
        # 第一步：将DWG转换为DXF
        logger.info("步骤1: 正在将DWG转换为DXF...")
        dxf_success = convert_dwg_to_dxf(dwg_path, temp_dxf_path)
        
        if not dxf_success:
            logger.error("DWG到DXF转换失败")
            return False
        
        # 检查临时DXF文件是否存在
        if not os.path.exists(temp_dxf_path):
            logger.error(f"临时DXF文件不存在: {temp_dxf_path}")
            return False
        
        # 第二步：读取DXF文件并转换为JPG
        logger.info("步骤2: 正在将DXF转换为JPG...")
        try:
            doc = ezdxf.readfile(temp_dxf_path)
            jpg_success = convert_dxf_to_jpg(doc, jpg_path, size, bg_color, line_color, dpi)
            
            if jpg_success:
                logger.info(f"DWG到JPG转换成功，输出文件: {jpg_path}")
            else:
                logger.error("DXF到JPG转换失败")
            
            return jpg_success
        except Exception as e:
            logger.error(f"读取DXF文件或转换为JPG时出错: {str(e)}")
            return False
        finally:
            # 清理临时文件和目录
            logger.info("清理临时文件...")
            try:
                if os.path.exists(temp_dxf_path):
                    os.remove(temp_dxf_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"清理临时文件时出错: {str(cleanup_error)}")
                
    except Exception as e:
        logger.error(f"DWG到JPG转换过程中发生错误: {str(e)}")
        return False

def convert_dxf_to_jpg(doc, output_path, size=3200, bg_color='white', line_color='black', dpi=600):
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