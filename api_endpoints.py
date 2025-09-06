import os
import tempfile
import time
import urllib.parse
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from logger_config import logger
from database import (db, get_dwg_files_from_database, record_conversion_to_database, 
                      insert_jpg_to_attachment, update_conversion_status)
from converter import converter_dwg_to_jpg

# 创建FastAPI应用实例
app = FastAPI(
    title="DWG到JPG转换器API",
    description="提供DWG文件转换为JPG的Web服务",
    version="1.0.0"
)

# 从环境变量获取临时目录配置，如果不存在则使用默认值
TEMP_DIR_PATH = os.getenv("TEMP_DIR", "temp")
# 确保临时目录存在，使用绝对路径
TEMP_DIR = Path(os.path.abspath(TEMP_DIR_PATH))
TEMP_DIR.mkdir(exist_ok=True)
logger.info(f"使用临时目录: {TEMP_DIR}")

# 定期检查和转换任务
async def periodic_check_and_convert():
    """定期从数据库检查需要转换的DWG文件并执行转换"""
    # 从环境变量获取检查间隔，如果不存在则使用默认值
    check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
    
    logger.info(f"启动定期检查任务，检查间隔: {check_interval} 秒")
    
    while True:
        try:
            logger.info("开始检查数据库中的DWG文件")
            
            # 从数据库获取需要转换的DWG文件
            dwg_files = get_dwg_files_from_database()
            
            if dwg_files:
                logger.info(f"找到 {len(dwg_files)} 个需要转换的DWG文件")
                
                # 逐一转换每个DWG文件
                for dwg_file in dwg_files:
                    order_id = dwg_file.get('id')
                    # 直接使用数据库中的FilePath作为相对路径
                    relative_dwg_path = dwg_file.get('FilePath')
                    
                    if order_id and relative_dwg_path:
                        logger.info(f"开始转换订单ID: {order_id} 的DWG文件: {relative_dwg_path} (相对路径)")
                        try:
                            # 传递相对路径而不是绝对路径
                            await convert_dwg_from_database(order_id, relative_dwg_path)
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"转换订单ID: {order_id} 的DWG文件失败: {error_msg}")
                            # 记录转换失败信息到数据库，使用相对路径
                            record_conversion_to_database(Path(relative_dwg_path).name, relative_dwg_path, "", "失败", 0, error_msg)
                    else:
                        logger.warning("找到无效的DWG文件记录: %s", dwg_file)
            else:
                logger.info("未找到需要转换的DWG文件")
            
        except Exception as e:
            logger.error(f"定期检查和转换任务出错: {str(e)}")
        
        # 等待指定的检查间隔
        logger.info(f"等待 {check_interval} 秒后再次检查")
        await asyncio.sleep(check_interval)

# 转换从数据库获取的DWG文件
async def convert_dwg_from_database(order_id, relative_dwg_path, skip_exists_check=False):
    """转换从数据库获取的DWG文件为JPG"""
    try:
        # 从环境变量中获取DWG文件路径前缀
        dwg_file_prefix = os.getenv("DWG_FILE_PREFIX", "")
        logger.info(f"DWG文件路径前缀: {dwg_file_prefix}")
        
        # 检查传入的relative_dwg_path是否已经是完整的绝对路径
        # 判断条件: 以驱动器字母开头(如D:)或者已经包含完整路径
        # 注意：在Windows上，os.path.isabs()会将以/或\开头的路径视为绝对路径，我们需要更精确的判断
        is_full_path = False
        if len(relative_dwg_path) >= 2 and relative_dwg_path[1] == ':' and relative_dwg_path[0].isalpha():
            is_full_path = True
        elif os.path.isabs(relative_dwg_path) and (len(relative_dwg_path) >= 2 and relative_dwg_path[1] == ':'):
            is_full_path = True
        
        # 如果已经是完整路径，直接使用；否则进行拼接
        if is_full_path:
            full_dwg_path = relative_dwg_path
            logger.info(f"DWG路径已包含完整路径，直接使用: {full_dwg_path}")
        else:
            # 拼接完整的DWG文件路径
            # 确保路径分隔符的一致性，在Windows环境下统一处理
            if dwg_file_prefix:
                # 标准化路径分隔符，将所有/替换为\
                normalized_prefix = dwg_file_prefix.replace('/', '\\')
                normalized_dwg_path = relative_dwg_path.replace('/', '\\')
                
                # 确保prefix以\结尾
                if not normalized_prefix.endswith('\\'):
                    normalized_prefix += '\\'
                
                # 移除relative_dwg_path开头的\（如果有）
                if normalized_dwg_path.startswith('\\'):
                    normalized_dwg_path = normalized_dwg_path[1:]
                
                # 拼接路径
                full_dwg_path = normalized_prefix + normalized_dwg_path
            else:
                # 如果没有设置前缀，直接使用原始路径
                full_dwg_path = relative_dwg_path
            
        logger.info(f"原始DWG路径(相对路径): {relative_dwg_path}, 完整DWG路径: {full_dwg_path}")
        
        # 检查文件是否存在（除非跳过检查）
        dwg_file_path = Path(full_dwg_path)
        if not skip_exists_check and not dwg_file_path.exists():
            logger.error(f"系统订单{order_id}DWG文件不存在: {full_dwg_path}")
            logger.error(f"系统订单{order_id}DWG文件相对路径: {relative_dwg_path}")
            # 更新数据库状态，表示文件不存在
            update_conversion_status(order_id, relative_dwg_path, "失败", "文件不存在")
            return
        
        # 生成JPG输出路径（与源文件相同目录）
        jpg_filename = f"{dwg_file_path.stem}.jpg"
        jpg_path = dwg_file_path.parent / jpg_filename
        
        logger.info(f"准备将DWG文件转换为JPG: {dwg_file_path} -> {jpg_path}")
        
        # 调用转换函数
        success = converter_dwg_to_jpg(str(dwg_file_path), str(jpg_path))
        
        if not success:
            logger.error(f"转换订单ID: {order_id} 的DWG文件失败: DWG到JPG转换失败")
            update_conversion_status(order_id, relative_dwg_path, "失败", "DWG到JPG转换失败")
            return
        
        # 验证JPG文件是否成功创建
        if not jpg_path.exists():
            logger.error(f"转换订单ID: {order_id} 的DWG文件失败: JPG文件未创建")
            update_conversion_status(order_id, relative_dwg_path, "失败", "JPG文件未创建")
            return
            
        # 获取文件大小
        jpg_size = jpg_path.stat().st_size
        if jpg_size == 0:
            logger.error(f"转换订单ID: {order_id} 的DWG文件失败: 创建的JPG文件为空")
            update_conversion_status(order_id, relative_dwg_path, "失败", "创建的JPG文件为空")
            return
            
        logger.info(f"成功将订单ID: {order_id} 的DWG文件转换为JPG，文件大小: {jpg_size} 字节")
        
        # 更新转换状态为成功
        update_conversion_status(order_id, relative_dwg_path, "成功")
        
        # 记录转换成功信息到数据库，使用相对路径
        record_conversion_to_database(dwg_file_path.name, relative_dwg_path, str(jpg_path), "成功", jpg_size)
        
        # 将生成的JPG文件插入到数据库附件表中
        try:
            # insert_jpg_to_attachment返回布尔值，表示操作是否成功
            success = insert_jpg_to_attachment(order_id, str(jpg_path), str(relative_dwg_path))
            if success:
                logger.info(f"成功将JPG文件插入到数据库附件表，订单ID: {order_id}")
            else:
                logger.warning(f"将JPG文件插入到数据库附件表失败，但不影响转换流程")
        except Exception as db_error:
            logger.error(f"插入JPG文件到数据库附件表失败: {str(db_error)}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"转换订单ID: {order_id} 的DWG文件失败: {error_msg}")
        
        # 记录转换失败信息到数据库，使用相对路径
        record_conversion_to_database(dwg_file_path.name if 'dwg_file_path' in locals() else "未知", 
                                     relative_dwg_path, "", "失败", 0, error_msg)

# API端点：手动触发数据库查询和转换任务
@app.post("/convert/database", tags=["数据库转换"])
async def convert_from_database(skip_exists_check: bool = False):
    """手动触发从数据库查询DWG文件并进行转换的任务
    
    参数:
    - skip_exists_check: 是否跳过文件存在性检查
    
    返回:
    - 任务执行状态和统计信息
    """
    try:
        logger.info(f"收到手动触发数据库转换任务的请求，skip_exists_check: {skip_exists_check}")
        
        # 执行查询获取需要转换的DWG文件
        dwg_files = get_dwg_files_from_database()
        
        if not dwg_files:
            logger.info("未找到需要转换的DWG文件")
            return {
                "status": "success",
                "message": "未找到需要转换的DWG文件",
                "total_files": 0,
                "converted_files": 0,
                "failed_files": 0
            }
        
        logger.info(f"找到 {len(dwg_files)} 个需要转换的DWG文件")
        
        # 统计信息
        stats = {
            "total_files": len(dwg_files),
            "converted_files": 0,
            "failed_files": 0,
            "failed_files_details": []
        }
        

        # 逐一转换每个DWG文件
        for dwg_file in dwg_files:
            order_id = dwg_file.get('id')
            # 使用相对路径变量名，与periodic_check_and_convert函数保持一致
            relative_dwg_path = dwg_file.get('FilePath')
            
            if order_id and relative_dwg_path:
                logger.info(f"开始转换订单ID: {order_id} 的DWG文件: {relative_dwg_path} (相对路径)")
                try:
                    # 转换文件，传递skip_exists_check参数
                    await convert_dwg_from_database(order_id, relative_dwg_path, skip_exists_check)
                    stats["converted_files"] += 1
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"转换订单ID: {order_id} 的DWG文件失败: {error_msg}")
                    stats["failed_files"] += 1
                    stats["failed_files_details"].append({
                        "order_id": order_id,
                        "file_path": relative_dwg_path,
                        "error": error_msg
                    })
            else:
                logger.warning(f"找到无效的DWG文件记录: {dwg_file}")
                stats["failed_files"] += 1
                
        logger.info(f"手动触发数据库转换任务完成: 总计 {stats['total_files']} 个文件，成功 {stats['converted_files']} 个，失败 {stats['failed_files']} 个")
        
        return {
            "status": "success",
            "message": f"数据库转换任务执行完成",
            "total_files": stats["total_files"],
            "converted_files": stats["converted_files"],
            "failed_files": stats["failed_files"],
            "failed_files_details": stats["failed_files_details"] if stats["failed_files"] > 0 else None
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"手动触发数据库转换任务失败: {error_msg}")
        raise HTTPException(status_code=500, detail=f"执行数据库转换任务失败: {error_msg}")

# API端点：DWG到JPG转换
@app.post("/convert/dwg-to-jpg", response_class=FileResponse)
async def convert_dwg_to_jpg_endpoint(order_id: int = None, file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """将DWG文件转换为JPG格式"""
    # 验证文件类型
    if not file.filename.lower().endswith(".dwg"):
        raise HTTPException(status_code=400, detail="仅支持DWG文件")
    
    try:
        # 保存上传的DWG文件到临时目录
        temp_filename = next(tempfile._get_candidate_names())
        dwg_path = TEMP_DIR / f"{temp_filename}.dwg"
        with open(dwg_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 验证文件是否成功保存
        if not dwg_path.exists():
            raise FileNotFoundError(f"无法保存上传的文件到: {dwg_path}")
        
        # 使用当前工作目录作为JPG输出路径，避免权限和路径解析问题
        jpg_path = Path(os.getcwd()) / f"{temp_filename}.jpg"
        logger.info(f"JPG输出路径设置为当前目录: {jpg_path}")
        
        logger.info(f"已保存上传文件到: {dwg_path}")
        
        # 使用新创建的包来转换DWG到JPG
        success = converter_dwg_to_jpg(str(dwg_path), str(jpg_path))
        
        if not success:
            raise Exception("DWG到JPG转换失败")
        
        # 验证JPG文件是否成功创建
        if not jpg_path.exists():
            raise FileNotFoundError(f"JPG文件未创建: {jpg_path}")
            
        # 获取文件大小作为额外验证
        jpg_size = jpg_path.stat().st_size
        if jpg_size == 0:
            raise ValueError(f"创建的JPG文件为空: {jpg_size} 字节")
            
        logger.info(f"成功将 {file.filename} 转换为JPG，文件大小: {jpg_size} 字节")
        
        # 记录转换成功信息到数据库
        try:
            insert_query = """
                INSERT INTO conversion_history (file_name, original_path, jpg_path, status, file_size)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_query(
                insert_query,
                (file.filename, str(dwg_path), str(jpg_path), "成功", jpg_size)
            )
            logger.info("转换记录已保存到数据库")
            
            # 将生成的JPG文件插入到数据库附件表中
            # 使用传入的订单ID（如果有）
            if order_id:
                try:
                    # insert_jpg_to_attachment返回布尔值，表示操作是否成功
                    success = insert_jpg_to_attachment(order_id, str(jpg_path), str(dwg_path))
                    if success:
                        logger.info(f"成功将JPG文件插入到数据库附件表，订单ID: {order_id}")
                    else:
                        logger.warning(f"将JPG文件插入到数据库附件表失败，但不影响转换流程")
                except Exception as db_error:
                    logger.error(f"插入JPG文件到数据库附件表失败: {str(db_error)}")
            else:
                logger.info("未提供订单ID，跳过插入附件表操作")
        except Exception as db_error:
            logger.error(f"保存转换记录到数据库失败: {str(db_error)}")
        
        # 添加后台任务，在响应返回后清理临时文件
        def cleanup_files():
            cleanup_delay = 300  # 延迟30秒清理文件，确保文件传输完成
            logger.info(f"等待{cleanup_delay}秒后开始清理文件，确保文件传输完成...")
            time.sleep(cleanup_delay)
            
            # 清理DWG文件
            if dwg_path and hasattr(dwg_path, 'exists') and dwg_path.exists():
                try:
                    dwg_path.unlink()
                    logger.info(f"已清理临时DWG文件: {dwg_path}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时DWG文件失败: {str(cleanup_error)}")
            
            # 清理JPG文件 - 检查当前工作目录和临时目录
            jpg_basename = None
            if jpg_path and hasattr(jpg_path, 'name'):
                jpg_basename = jpg_path.name
            
            # 检查可能的JPG文件位置
            jpg_locations = []
            if jpg_path:
                jpg_locations.append(jpg_path)
            if jpg_basename:
                jpg_locations.append(Path(os.getcwd()) / jpg_basename)
                jpg_locations.append(TEMP_DIR / jpg_basename)
                jpg_locations.append(Path(os.environ.get('TEMP', '')) / jpg_basename)
            
            # 尝试清理所有可能的JPG文件
            for location in jpg_locations:
                if hasattr(location, 'exists') and location.exists():
                    try:
                        location.unlink()
                        logger.info(f"已清理JPG文件: {location}")
                    except Exception as cleanup_error:
                        logger.warning(f"清理JPG文件失败: {location}，错误: {str(cleanup_error)}")
            
            if not any(hasattr(loc, 'exists') and loc.exists() for loc in jpg_locations):
                logger.info(f"未找到需要清理的JPG文件，文件基础名: {jpg_basename}")
        
        # 注册后台清理任务
        background_tasks.add_task(cleanup_files)
        
        # 在返回前等待并验证JPG文件是否存在
        max_wait_time = 30  # 最大等待时间（秒）
        check_interval = 0.5  # 检查间隔（秒）
        waited_time = 0
        
        # 循环检查文件是否存在、大小大于最小阈值且稳定（不再变化）
        stable_size_count = 0
        required_stable_checks = 3  # 需要连续3次检测到相同大小才算稳定
        last_size = -1
        MIN_JPG_SIZE = 500  # 设置最小JPG文件大小阈值（字节）
        
        while waited_time < max_wait_time:
            if jpg_path.exists():
                jpg_size = jpg_path.stat().st_size
                
                # 检查文件大小是否大于最小阈值
                if jpg_size >= MIN_JPG_SIZE:
                    # 检查文件大小是否稳定（不再变化）
                    if jpg_size == last_size:
                        stable_size_count += 1
                        logger.info(f"JPG文件大小稳定({stable_size_count}/{required_stable_checks}): {jpg_path}，大小: {jpg_size} 字节")
                        
                        # 如果文件大小连续稳定了指定次数，认为文件已完全写入完成
                        if stable_size_count >= required_stable_checks:
                            logger.info(f"JPG文件已完全生成并准备提供服务: {jpg_path}，大小: {jpg_size} 字节")
                            break
                    else:
                        # 文件大小仍在变化，重置稳定计数
                        stable_size_count = 0
                        last_size = jpg_size
                        logger.info(f"JPG文件正在生成中，当前大小: {jpg_size} 字节，等待: {waited_time:.1f}秒")
                elif jpg_size > 0:
                    # 文件大小小于最小阈值，可能是临时文件或空文件头
                    logger.warning(f"JPG文件大小过小（{jpg_size}字节），可能不是有效的JPG文件，继续等待... 当前等待: {waited_time:.1f}秒")
                    # 不增加稳定计数，继续等待文件增长
                    last_size = jpg_size
                else:
                    logger.info(f"JPG文件已存在但大小为0，等待文件写入完成... 当前等待: {waited_time:.1f}秒")
            else:
                logger.info(f"JPG文件尚未生成，等待中... 当前等待: {waited_time:.1f}秒")
            
            time.sleep(check_interval)
            waited_time += check_interval
        
        # 再次验证文件是否存在且大小符合要求
        if not jpg_path.exists():
            raise FileNotFoundError(f"JPG文件在等待{max_wait_time}秒后仍未生成: {jpg_path}")
        
        jpg_size = jpg_path.stat().st_size
        if jpg_size < MIN_JPG_SIZE:
            raise ValueError(f"JPG文件大小过小（{jpg_size}字节），可能不是有效的JPG文件: {jpg_path}")
        
        logger.info(f"返回文件路径: {str(jpg_path)}")
        # 导入URL编码模块
        
        # 对文件名进行URL编码，解决中文文件名在HTTP头部的编码问题
        encoded_filename = urllib.parse.quote(f"{file.filename.rsplit('.', 1)[0]}.jpg")
        
        # 返回转换后的JPG文件，使用正确的HTTP头
        return FileResponse(
            path=str(jpg_path),  # 直接使用字符串路径
            filename=f"{file.filename.rsplit('.', 1)[0]}.jpg",
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"attachment; filename={encoded_filename}"
                # 注意：filename*参数在某些浏览器中可能需要，但大多数现代浏览器支持filename参数的UTF-8编码
            }
        )
        
    except Exception as e:
        logger.error(f"转换文件时出错: {str(e)}")
        
        # 记录转换失败信息到数据库
        try:
            if 'file' in locals() and 'dwg_path' in locals() and hasattr(dwg_path, '__str__'):
                insert_query = """
                INSERT INTO conversion_history (file_name, original_path, jpg_path, status, error_message)
                VALUES (?, ?, ?, ?, ?)
                """
                jpg_path_str = str(jpg_path) if 'jpg_path' in locals() and hasattr(jpg_path, '__str__') else ""
                db.execute_query(
                    insert_query,
                    (file.filename, str(dwg_path), jpg_path_str, "失败", str(e))
                )
                logger.info("转换失败记录已保存到数据库")
        except Exception as db_error:
            logger.error(f"保存转换失败记录到数据库失败: {str(db_error)}")
        # 转换失败时立即清理临时文件
        if 'dwg_path' in locals() and dwg_path.exists():
            dwg_path.unlink()
        if 'jpg_path' in locals() and jpg_path.exists():
            jpg_path.unlink()
        
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")

# API根端点
@app.get("/")
async def root():
    """API根端点，提供基本信息"""
    return {
        "message": "欢迎使用DWG到JPG转换器API",
        "endpoints": [
            "/convert/dwg-to-jpg (POST) - 上传DWG文件转换为JPG",
            "/conversion-history (GET) - 获取转换历史记录",
            "/convert/database (POST) - 手动触发从数据库查询DWG文件并进行转换的任务"
        ]
    }

# 获取转换历史记录
@app.get("/conversion-history")
async def get_conversion_history(page: int = 1, page_size: int = 20, status: str = None):
    """获取转换历史记录
    
    参数:
    - page: 页码（默认为1）
    - page_size: 每页记录数（默认为20）
    - status: 过滤状态（可选：成功/失败）
    """
    try:
        offset = (page - 1) * page_size
        query_parts = [
            "SELECT id, file_name, original_path, jpg_path, conversion_time, status, file_size, error_message",
            "FROM conversion_history",
            "WHERE 1=1"
        ]
        params = []
        
        # 添加状态过滤条件
        if status:
            query_parts.append("AND status = ?")
            params.append(status)
        
        # 添加排序和分页
        query_parts.append("ORDER BY conversion_time DESC")
        query_parts.append(f"OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY")
        
        # 执行查询获取数据
        query = "\n".join(query_parts)
        results = db.execute_query(query, params)
        
        # 查询总记录数
        count_query = "SELECT COUNT(*) AS total FROM conversion_history WHERE 1=1"
        if status:
            count_query += " AND status = ?"
        total_result = db.execute_query(count_query, params if status else None)
        total_count = total_result[0]['total'] if total_result else 0
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "data": results
        }
    except Exception as e:
        logger.error(f"获取转换历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取转换历史记录失败: {str(e)}")

# 导入必要的模块
import asyncio
from database import db

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化任务"""
    logger.info("DWG到JPG转换器API正在启动...")
    
    # 初始化数据库连接
    if not db.conn or db.conn.closed:
        db.connect()
    
    # 启动定期检查任务
    # 注意：如果在生产环境中使用，应该考虑使用后台任务管理而不是简单的异步任务
    # 这里使用一个标志来避免在测试或开发环境中启动多个任务
    if os.getenv("ENABLE_PERIODIC_TASK", "true").lower() == "true":
        logger.info("启动定期检查和转换任务")
        # 使用create_task而不是直接await，这样应用可以继续启动
        asyncio.create_task(periodic_check_and_convert())
    
    logger.info("DWG到JPG转换器API已成功启动")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的清理任务"""
    try:
        db.disconnect()
        logger.info("应用已关闭，数据库连接已断开")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {str(e)}")