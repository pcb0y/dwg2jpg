import os
import pythoncom
import win32com.client
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('basic_dwg2pdf')

def safe_com_call(func, *args, **kwargs):
    """安全地调用COM对象方法，处理异常"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"COM调用失败: {str(e)}")
        raise

def convert_with_autocad_basic(dwg_path: Path, pdf_path: Path):
    """最基础的AutoCAD COM接口将DWG文件转换为PDF版本，增强了路径处理和错误处理"""
    # 确保路径是绝对路径并使用正确的Windows格式
    absolute_dwg_path = os.path.abspath(str(dwg_path)).replace('/', '\\')
    absolute_pdf_path = os.path.abspath(str(pdf_path)).replace('/', '\\')
    
    logger.info(f"开始基础版DWG到PDF转换:")
    logger.info(f"- DWG文件: {absolute_dwg_path}")
    logger.info(f"- PDF输出: {absolute_pdf_path}")
    logger.info(f"- 保存目录: {os.path.dirname(absolute_dwg_path)}")
    
    # 验证文件是否存在
    if not os.path.exists(absolute_dwg_path):
        raise FileNotFoundError(f"未找到DWG文件: {absolute_dwg_path}")
    
    # 初始化COM
    pythoncom.CoInitialize()
    
    acad = None
    doc = None
    
    try:
        # 定义AutoCAD版本列表（必须在使用前定义）
        acad_versions = [
            "AutoCAD.Application",  # 默认版本
            "AutoCAD.Application.24",  # AutoCAD 2022
            "AutoCAD.Application.23",  # AutoCAD 2021
            "AutoCAD.Application.22",  # AutoCAD 2020
        ]
        
        # 创建AutoCAD应用实例，尝试不同版本
        logger.info("尝试创建AutoCAD应用实例...")
        acad = None
        version_error = ""
        
        for version_id in acad_versions:
            try:
                logger.info(f"尝试连接AutoCAD版本: {version_id}")
                acad = win32com.client.Dispatch(version_id)
                acad.Visible = False
                logger.info(f"已成功创建AutoCAD应用实例 ({version_id})")
                break  # 成功后跳出循环
            except Exception as e:
                version_error = str(e)
                logger.warning(f"连接AutoCAD版本 {version_id} 失败: {version_error}")
                
        # 如果无法连接任何AutoCAD版本
        if acad is None:
            logger.error(f"无法创建AutoCAD应用实例，尝试了以下版本: {', '.join(acad_versions)}")
            logger.error(f"最后一个错误: {version_error}")
            # 尝试其他可能的方式
            try:
                logger.info("尝试使用ProgID创建AutoCAD应用...")
                acad = win32com.client.gencache.EnsureDispatch("AutoCAD.Application")
                acad.Visible = False
                logger.info("已成功通过ProgID创建AutoCAD应用实例")
            except Exception as e:
                logger.error(f"所有创建AutoCAD应用实例的尝试都失败: {str(e)}")
                raise Exception(f"无法启动AutoCAD应用: {str(e)}")
        
        # 尝试打开DWG文件，增加路径处理选项
        doc = None
        retry_count = 0
        max_retries = 3  # 增加重试次数
        error_message = ""
        
        # 尝试多种路径格式和编码
        path_formats = [
            absolute_dwg_path,  # 标准绝对路径
            absolute_dwg_path.replace('\\', '\\\\'),  # UNC格式路径
            absolute_dwg_path.replace('\\', '/'),  # 斜杠格式路径
        ]
        
        # 添加非ASCII字符的路径处理选项
        try:
            # 尝试使用原始字符串路径
            raw_path = r"{}".format(absolute_dwg_path)
            if raw_path not in path_formats:
                path_formats.append(raw_path)
            
            # 对于包含非ASCII字符的路径，尝试使用短路径
            if any(ord(c) > 127 for c in absolute_dwg_path):
                logger.info(f"检测到非ASCII字符路径，尝试获取短路径")
                try:
                    import ctypes
                    buffer = ctypes.create_unicode_buffer(512)
                    if ctypes.windll.kernel32.GetShortPathNameW(absolute_dwg_path, buffer, 512):
                        short_path = buffer.value
                        if short_path and short_path not in path_formats:
                            path_formats.append(short_path)
                            logger.info(f"已获取短路径: {short_path}")
                except Exception as e:
                    logger.warning(f"获取短路径失败: {str(e)}")
            
            # 处理长路径 (超过260个字符)
            if len(absolute_dwg_path) > 260:
                logger.info(f"路径过长({len(absolute_dwg_path)}字符)，尝试使用长路径前缀")
                # 添加长路径前缀
                if not absolute_dwg_path.startswith('\\\\?\\'):
                    long_path = '\\\\?\\' + absolute_dwg_path
                    if long_path not in path_formats:
                        path_formats.append(long_path)
                        logger.info(f"已添加长路径前缀: {long_path}")
        except Exception as e:
            logger.warning(f"处理特殊路径格式时出错: {str(e)}")
        

        
        # 首先尝试所有路径格式
        format_attempt = 0
        while format_attempt < len(path_formats) and doc is None:
            current_path = path_formats[format_attempt]
            try:
                logger.info(f"尝试打开DWG文件 (格式 {format_attempt+1}/{len(path_formats)}): {current_path}")
                doc = safe_com_call(acad.Documents.Open, current_path)
                
                if doc is not None:
                    logger.info("已成功在AutoCAD中打开DWG文件")
                    break
            except Exception as e:
                error_message = str(e)
                logger.warning(f"使用格式 {format_attempt+1} 打开DWG文件失败: {error_message}")
            
            format_attempt += 1
            import time
            time.sleep(0.5)  # 短暂延迟后重试
        
        # 如果所有路径格式都失败，尝试切换工作目录方法
        if doc is None and retry_count < max_retries:
            retry_count += 1
            try:
                logger.info(f"尝试打开DWG文件 (方法2 - 切换工作目录): {os.path.basename(absolute_dwg_path)}")
                original_dir = os.getcwd()
                os.chdir(os.path.dirname(absolute_dwg_path))
                try:
                    # 尝试使用短文件名
                    short_name = os.path.basename(absolute_dwg_path)
                    logger.info(f"使用短文件名: {short_name}")
                    doc = safe_com_call(acad.Documents.Open, short_name)
                finally:
                    os.chdir(original_dir)  # 恢复原工作目录
                
                if doc is not None:
                    logger.info("已成功在AutoCAD中打开DWG文件 (通过切换工作目录)")
            except Exception as e:
                error_message = str(e)
                logger.warning(f"通过切换工作目录打开DWG文件失败: {error_message}")
        
        # 如果所有尝试都失败，使用简化的SendCommand方法作为最后的备选方案
        if doc is None and retry_count < max_retries:
            retry_count += 1
            try:
                logger.info(f"尝试打开DWG文件 (方法3 - 简化的SendCommand): {absolute_dwg_path}")
                
                # 准备SendCommand命令，使用最简单的格式
                send_path = absolute_dwg_path.replace('\\', '\\\\')
                command = f'OPEN "{send_path}"\n'
                
                logger.info(f"发送简化的AutoCAD命令: {command}")
                
                # 只使用最基本的SendCommand调用
                try:
                    # 确保acad对象有效
                    if acad:
                        acad.SendCommand(command)
                        logger.info("命令已发送到AutoCAD")
                except Exception as cmd_error:
                    logger.warning(f"SendCommand调用失败: {str(cmd_error)}")
                
                # 给AutoCAD一些时间来处理命令
                import time
                time.sleep(4)  # 增加等待时间
                
                # 简化检查逻辑，只尝试获取ActiveDocument
                try:
                    if acad and hasattr(acad, 'ActiveDocument'):
                        doc = acad.ActiveDocument
                        if doc:
                                logger.info(f"已获取AutoCAD活动文档: {doc.Name}")
                                # 不检查文档名称，只要能获取到文档对象就视为成功
                except Exception as check_error:
                    logger.warning(f"检查AutoCAD文档时出错: {str(check_error)}")
            except Exception as e:
                error_message = str(e)
                logger.warning(f"通过简化的SendCommand打开DWG文件失败: {error_message}")
        
        # 如果所有尝试都失败，抛出异常
        if doc is None:
            logger.error(f"所有打开DWG文件的尝试都失败: {error_message}")
            raise Exception(f"无法打开DWG文件: {absolute_dwg_path}, 错误: {error_message}")
        
        # 验证文档对象有效性
        try:
            # 检查文档是否有基本属性
            doc_name = doc.Name
            logger.info(f"成功获取文档名称: {doc_name}")
            
            # 尝试获取布局前，先验证文档是否完全加载
            try:
                # 检查文档是否包含模型空间
                model_space = doc.ModelSpace
                if model_space.Count >= 0:
                    logger.info(f"文档模型空间包含 {model_space.Count} 个对象")
            except Exception as ms_error:
                logger.warning(f"无法访问模型空间: {str(ms_error)}")
                # 模型空间访问失败不一定意味着文档无效，继续尝试
            
            # 获取当前布局，增加错误处理
            layout = None
            try:
                layout = doc.ActiveLayout
                logger.info(f"成功获取活动布局")
            except Exception as layout_error:
                logger.error(f"获取活动布局失败: {str(layout_error)}")
                # 尝试其他方式获取布局
                try:
                    # 尝试获取第一个布局
                    layouts = doc.Layouts
                    if layouts.Count > 0:
                        layout = layouts.Item(0)
                        logger.info(f"成功获取第一个布局: {layout.Name}")
                    else:
                        raise Exception("文档中没有可用的布局")
                except Exception as alt_layout_error:
                    logger.error(f"无法获取任何布局: {str(alt_layout_error)}")
                    raise Exception(f"AutoCAD文档无效: 无法访问布局, 错误: {str(alt_layout_error)}")
        except Exception as doc_error:
            logger.error(f"验证文档有效性失败: {str(doc_error)}")
            raise Exception(f"AutoCAD文档无效: {str(doc_error)}")
        
        # 设置打印设备
        try:
            safe_com_call(lambda: setattr(layout, "ConfigName", "DWG To PDF.pc3"))
            logger.info("已设置打印设备为DWG To PDF.pc3")
        except Exception as e:
            logger.warning(f"设置打印设备失败，尝试使用备用配置: {str(e)}")
            try:
                # 尝试备用PDF打印机配置
                safe_com_call(lambda: setattr(layout, "ConfigName", "AutoCAD PDF (General Documentation).pc3"))
                logger.info("已设置打印设备为AutoCAD PDF (General Documentation).pc3")
            except Exception as e2:
                logger.error(f"设置打印设备失败: {str(e2)}")
                # 继续尝试，因为有些系统可能有默认配置
        
        # 设置打印到文件
        safe_com_call(lambda: setattr(layout, "PlotToFile", True))
        logger.info("已设置打印到文件模式")
        
        # 设置不显示对话框
        plot = doc.Plot
        safe_com_call(lambda: setattr(plot, "QuietErrorMode", True))
        
        # 确保目标目录存在
        pdf_dir = os.path.dirname(absolute_pdf_path)
        if not os.path.exists(pdf_dir):
            try:
                os.makedirs(pdf_dir)
                logger.info(f"已创建PDF输出目录: {pdf_dir}")
            except Exception as e:
                logger.error(f"创建PDF输出目录失败: {str(e)}")
        
        # 执行打印到PDF
        logger.info(f"准备执行打印到文件: {absolute_pdf_path}")
        
        # 尝试打印，增加错误处理
        print_success = False
        for print_attempt in range(2):
            try:
                safe_com_call(lambda: plot.PlotToFile(absolute_pdf_path))
                print_success = True
                logger.info(f"成功执行PlotToFile方法 (尝试 {print_attempt+1})")
                break
            except Exception as e:
                logger.warning(f"打印失败 (尝试 {print_attempt+1}/2): {str(e)}")
                if print_attempt == 0:
                    # 第一次失败后，重新获取plot对象
                    logger.info("重新获取plot对象并再次尝试...")
                    plot = doc.Plot
                    safe_com_call(lambda: setattr(plot, "QuietErrorMode", True))
                else:
                    # 所有打印尝试都失败
                    logger.error(f"所有打印尝试都失败: {str(e)}")
                    raise
        
        # 验证文件是否创建
        if os.path.exists(absolute_pdf_path):
            file_size = os.path.getsize(absolute_pdf_path)
            logger.info(f"PDF文件创建成功，大小: {file_size} 字节")
            
            # 检查文件大小是否合理
            if file_size < 500:  # 设置最小文件大小阈值
                logger.warning(f"PDF文件可能不完整，大小过小: {file_size} 字节")
        else:
            logger.error(f"PDF文件未创建成功")
            raise FileNotFoundError(f"PDF文件未创建: {absolute_pdf_path}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"AutoCAD转换错误: {error_msg}")
        # 提供更详细的错误信息
        if '<unknown>.Open' in error_msg:
            logger.error("错误分析: 可能是AutoCAD无法识别该DWG文件格式或文件已损坏")
        raise Exception(f"AutoCAD转换错误: {error_msg}")
    
    finally:
        # 关闭文档
        if doc is not None:
            try:
                doc.Close(False)
                logger.info("AutoCAD文档已关闭")
            except Exception as e:
                logger.warning(f"关闭AutoCAD文档时出错: {str(e)}")
        
        # 释放COM资源
        pythoncom.CoUninitialize()
        logger.info("COM资源已释放")

if __name__ == "__main__":
    # 示例用法
    try:
        dwg_path = Path(r"C:\path\to\your\drawing.dwg")
        pdf_path = Path(r"C:\path\to\output\drawing.pdf")
        convert_with_autocad_basic(dwg_path, pdf_path)
        print("转换完成")
    except Exception as e:
        print(f"转换失败: {str(e)}")