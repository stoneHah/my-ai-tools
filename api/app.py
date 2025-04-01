"""
FastAPI主应用
整合所有API路由，提供API服务
"""
import os
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.ai.router import router as ai_router
from api.media.router import router as media_router
from api.asr.router import router as asr_router
from api.tts.router import router as tts_router
from api.tts.clone_router import router as tts_clone_router
from ai_services.coze_service import register_coze_service
from ai_services.coze_workflow import register_coze_workflow_service
from ai_services.asr.registry import register_all_asr_services
from ai_services.tts.registry import register_all_tts_services
from ai_services.tts.clone_registry import register_all_voice_clone_services
from ai_services.storage.registry import register_all_storage_services
from api.middleware.response import APIResponseMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
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

# 添加响应中间件
app.add_middleware(
    APIResponseMiddleware,
    exclude_paths=["/docs", "/redoc", "/openapi.json", "/tts/synthesize/stream"],
    exclude_content_types=["application/octet-stream", "audio/", "video/", "image/"]
)

# 注册AI服务
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
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
    
    # 注册所有ASR服务
    asr_services = register_all_asr_services()
    if asr_services:
        for name, service in asr_services.items():
            print(f"已注册ASR服务: {service.service_name} (类型: {service.service_type})")
    else:
        print("未注册ASR服务，请检查环境变量DASHSCOPE_API_KEY是否已设置")
    
    # 注册所有TTS服务
    tts_services = register_all_tts_services()
    if tts_services:
        for name, service in tts_services.items():
            print(f"已注册TTS服务: {service.service_name} (类型: {service.service_type})")
    else:
        print("未注册TTS服务，请检查环境变量VOLCENGINE_TTS_APPID、VOLCENGINE_TTS_TOKEN和VOLCENGINE_TTS_CLUSTER是否已设置")
    
    # 注册所有语音克隆服务
    voice_clone_services = register_all_voice_clone_services()
    if voice_clone_services:
        for name, service in voice_clone_services.items():
            print(f"已注册语音克隆服务: {service.service_name} (类型: {service.clone_service_type})")
    else:
        print("未注册语音克隆服务，请检查环境变量DASHSCOPE_API_KEY是否已设置")
    
    # 注册所有存储服务
    register_all_storage_services()

# 添加路由
app.include_router(ai_router)
app.include_router(media_router)
app.include_router(asr_router)
app.include_router(tts_router)
app.include_router(tts_clone_router)

# 健康检查端点
@app.get("/health", tags=["health"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "ai-platform"}

# 直接运行此文件时启动服务器
if __name__ == "__main__":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
