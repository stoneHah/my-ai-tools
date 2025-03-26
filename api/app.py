"""
FastAPI主应用
整合所有API路由，提供API服务
"""
import os
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ai_router import router as ai_router
from api.media_router import router as media_router
from api.asr_router import router as asr_router
from ai_services.coze_service import register_coze_service
from ai_services.coze_workflow import register_coze_workflow_service
from ai_services.dashscope_service import register_dashscope_asr_service

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 创建FastAPI应用
app = FastAPI(
    title="AI中台服务",
    description="提供统一的API接口访问各种AI服务，支持流式和非流式响应",
    version="1.0.0"
)

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册AI服务
def register_services():
    """注册所有AI服务"""
    # 注册Coze服务
    coze_service = register_coze_service()
    if coze_service:
        print(f"已注册服务: {coze_service.service_name} (类型: {coze_service.service_type})")
    else:
        print("未注册Coze服务，请检查环境变量COZE_API_TOKEN是否已设置")
    
    # 注册Coze工作流服务
    coze_workflow_service = register_coze_workflow_service()
    if coze_workflow_service:
        print(f"已注册服务: {coze_workflow_service.service_name} (类型: {coze_workflow_service.service_type})")
    else:
        print("未注册Coze工作流服务，请检查环境变量COZE_API_TOKEN是否已设置")
    
    # 注册阿里云百炼语音识别服务
    dashscope_asr_service = register_dashscope_asr_service()
    if dashscope_asr_service:
        print(f"已注册服务: {dashscope_asr_service.service_name} (类型: {dashscope_asr_service.service_type})")
    else:
        print("未注册阿里云百炼语音识别服务，请检查环境变量DASHSCOPE_API_KEY是否已设置")
    
    # 在这里注册其他AI服务
    # ...

# 启动时注册服务
register_services()

# 添加路由
app.include_router(ai_router)
app.include_router(media_router)
app.include_router(asr_router)

# 健康检查端点
@app.get("/health", tags=["health"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "ai-platform"}

# 直接运行此文件时启动服务器
if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
