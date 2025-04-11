"""
主应用程序
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import ResponseValidationError

from api.ai.router import router as ai_router
from api.image.router import router as image_router
from api.media.router import router as media_router
from api.asr.router import router as asr_router
from api.tts.router import router as tts_router
from api.tts.clone_router import router as tts_clone_router
from api.video.router import router as video_router

from db.service.task_service import TaskService
from db.config import get_db, init_db
from common.exceptions import BusinessException
from api.middleware.response import APIResponseMiddleware
from api.middleware.exception_handler import BusinessExceptionMiddleware
from api.middleware.request_logging import RequestLoggingMiddleware
from scripts.task_scheduler import TaskScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI服务中台",
    description="提供统一的AI服务接口",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加业务异常处理中间件（必须放在最外层，优先捕获异常）
app.add_middleware(BusinessExceptionMiddleware)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 添加响应中间件
app.add_middleware(
    APIResponseMiddleware,
    exclude_paths=["/docs", "/redoc", "/openapi.json", "/tts/synthesize/stream"],
    exclude_content_types=["application/octet-stream", "audio/", "video/", "image/"]
)


# 添加响应中间件
app.add_middleware(
    APIResponseMiddleware,
    exclude_paths=["/docs", "/redoc", "/openapi.json"],
    exclude_content_types=["application/octet-stream", "audio/", "video/", "image/", "multipart/form-data"]
)

# 全局任务服务实例
_task_service: Optional[TaskService] = None
# 全局任务调度器实例
_task_scheduler: Optional[TaskScheduler] = None


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器，捕获所有未处理的异常"""
    # 记录异常信息
    error_msg = f"全局异常: {str(exc)}, 类型: {type(exc).__name__}"
    logger.error(error_msg, exc_info=True)
    
    # 针对不同类型的异常返回不同的响应
    if isinstance(exc, BusinessException):
        # 业务异常
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=exc.to_dict()
        )
    elif isinstance(exc, Exception):
        # 其他所有异常
        import traceback
        stack_trace = traceback.format_exc()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,  # 使用200状态码，保持与业务异常一致
            content={
                "code": ErrorCode.GENERAL_ERROR,
                "message": f"系统错误: {str(exc)}",
                "data": {
                    "error_type": type(exc).__name__,
                    "stack_trace": stack_trace if os.getenv("DEBUG", "false").lower() == "true" else None
                }
            }
        )
    
    # 这里永远不会执行到，但为了类型检查添加
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "未知错误"}
    )


@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    global _task_service, _task_scheduler
    
    logger.info("应用启动")
    
    # 初始化数据库
    init_db()
    
    # 创建任务服务实例
    task_service = TaskService(next(get_db()))
    _task_service = task_service
    
    # 注册所有服务
    logger.info("正在注册AI服务...")
    
    # 注册Coze聊天服务
    from ai_services.coze_service import register_coze_service
    coze_service = register_coze_service()
    if coze_service:
        logger.info(f"已注册Coze聊天服务: {coze_service.service_name}")
    
    # 注册Coze工作流服务
    from ai_services.coze_workflow import register_coze_workflow_service
    workflow_service = register_coze_workflow_service()
    if workflow_service:
        logger.info(f"已注册Coze工作流服务: {workflow_service.service_name}")
    
    # 注册图像服务
    from ai_services.image.registry import register_all_image_services
    register_all_image_services(task_service)
    
    # 注册语音识别服务
    from ai_services.asr.registry import register_all_asr_services
    register_all_asr_services()
    
    # 注册语音合成服务
    from ai_services.tts.registry import register_all_tts_services
    register_all_tts_services()
    
    # 注册语音克隆服务
    from ai_services.tts.clone_registry import register_all_voice_clone_services
    register_all_voice_clone_services()
    
    # 注册存储服务
    from ai_services.storage.registry import register_all_storage_services
    register_all_storage_services()
    
    # 注册视频生成服务
    from ai_services.video.registry import register_all_video_services
    register_all_video_services(task_service)
    
    logger.info("所有服务注册完成")
    
    # 启动任务调度器
    logger.info("正在启动任务调度器...")
    _task_scheduler = TaskScheduler(interval=60)  # 每60秒检查一次任务状态
    _task_scheduler.start()
    logger.info("任务调度器已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件
    """
    global _task_scheduler
    
    # 停止任务调度器
    if _task_scheduler:
        logger.info("正在停止任务调度器...")
        _task_scheduler.stop()
        logger.info("任务调度器已停止")
    
    logger.info("应用关闭")


# 注册路由
# app.include_router(ai_router)
# app.include_router(media_router)
# app.include_router(asr_router)
# app.include_router(tts_router)
# app.include_router(tts_clone_router)
# app.include_router(image_router)
app.include_router(video_router)


@app.get("/")
async def root():
    """
    根路径
    
    Returns:
        欢迎信息
    """
    return {"message": "欢迎使用AI服务中台"}


@app.get("/health")
async def health():
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {"status": "ok"}
