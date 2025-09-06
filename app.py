import os
from dotenv import load_dotenv
import uvicorn
from logger_config import logger
from api_endpoints import app

# 加载.env文件中的环境变量
load_dotenv()

if __name__ == "__main__":
    # 从环境变量获取端口号，如果不存在则使用默认值
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"启动DWG到JPG转换器API服务，监听地址: {host}:{port}")
    
    # 启动FastAPI应用
    # 使用reload=True在开发环境下启用热重载，但在生产环境中应设置为False
    uvicorn.run(
        "api_endpoints:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )