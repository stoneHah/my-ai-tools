"""
AI中台服务启动脚本
"""
import os
import uvicorn
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"启动AI中台服务，地址: {host}:{port}")
    
    # 启动FastAPI应用
    uvicorn.run(
        "api.app:app", 
        host=host, 
        port=port, 
        reload=True
    )
