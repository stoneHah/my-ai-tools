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

from api.image.router import router as image_router
from db.service.task_service import TaskService
from db.config import get_db, init_db
from common.exceptions import BusinessException

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

# 全局任务服务实例
_task_service: Optional[TaskService] = None


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
                "code": "SYSTEM_ERROR",
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
    logger.info("应用启动")
    
    # 初始化数据库
    init_db()
    
    # 创建任务服务实例
    task_service = TaskService(next(get_db()))
    
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
    
    logger.info("所有服务注册完成")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件
    """
    logger.info("应用关闭")


# 注册路由
app.include_router(image_router)


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
