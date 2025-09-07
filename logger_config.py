import os
import logging
import logging.handlers
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建logger对象
logger = logging.getLogger(__name__)

# 检查是否设置了日志文件环境变量
LOG_FILE = os.getenv("LOG_FILE")
if LOG_FILE:
    # 确保日志目录存在
    # 如果LOG_FILE是目录，则使用默认文件名
    if os.path.isdir(LOG_FILE) or not os.path.splitext(LOG_FILE)[1]:
        # 确保目录存在
        log_dir = LOG_FILE if os.path.isdir(LOG_FILE) else os.path.dirname(LOG_FILE) or '.'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # 生成带日期的日志文件名，格式为：app_2025-09-07.log
        current_date = datetime.now().strftime('%Y-%m-%d')
        log_file_path = os.path.join(log_dir, f'app_{current_date}.log')
    else:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = LOG_FILE
    
    # 使用基本的FileHandler，因为TimedRotatingFileHandler在Python 3.8中不支持自定义日期格式
    # 这种方式会在每次应用启动时创建一个新的带日期的日志文件
    file_handler = logging.FileHandler(
        log_file_path,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)