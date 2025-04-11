"""
视频生成API路由
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ai_services.video.base import VideoServiceBase
from ai_services.video.registry import VideoServiceRegistry
from api.video.models import (
    ImageToVideoRequest, 
    CreateVideoTaskResponse,
    VideoTaskResultRequest,
    VideoTaskResultResponse,
    VideoServicesListResponse
)
from db.service import TaskService
from api.utils import get_task_service
from common.exceptions import BusinessException, ResourceNotFoundException, AIServiceError
from common.utils import normalize_response

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/video",
    tags=["video"],
    responses={404: {"description": "服务不存在"}}
)


@router.post("/task/create", response_model=CreateVideoTaskResponse)
async def create_video_task(
    request: ImageToVideoRequest,
    task_service: TaskService = Depends(get_task_service)
):
    """
    创建图生视频任务
    
    根据提供的提示词和图片创建视频生成任务，返回任务ID
    """
    service_name = request.service_name
    service = VideoServiceRegistry.get_service(service_name)
    
    if not service:
        raise ResourceNotFoundException(
            resource_type="视频生成服务",
            resource_id=service_name,
            message=f"视频生成服务 '{service_name}' 不存在"
        )
    
    try:
        # 创建任务
        task_dict = await service.create_image_to_video_task(
            prompt=request.prompt,
            image_url=request.image_url,
            ratio=request.ratio,
            duration=request.duration,
            model=request.model,
            parameters=request.parameters
        )
        
        # 从字典中获取数据
        return normalize_response({
            "task_id": task_dict["task_id"],
            "status": task_dict["status"],
            "created_at": task_dict["created_at"]
        })
    except BusinessException as e:
        # 业务异常会被全局异常处理器捕获
        raise
    except Exception as e:
        # 其他异常转换为业务异常
        logger.error(f"创建视频生成任务失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"创建视频生成任务失败: {str(e)}",
            exception=e
        )


@router.post("/task/result", response_model=VideoTaskResultResponse)
async def get_video_task_result(
    request: VideoTaskResultRequest,
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取视频生成任务结果
    
    根据任务ID获取视频生成任务的结果
    """
    task = task_service.get_task(request.task_id)
    if not task:
        raise ResourceNotFoundException(
            resource_type="任务",
            resource_id=request.task_id,
            message=f"任务 '{request.task_id}' 不存在"
        )
    
    service_name = task.service_name
    service = VideoServiceRegistry.get_service(service_name)
    
    if not service:
        raise ResourceNotFoundException(
            resource_type="视频生成服务",
            resource_id=service_name,
            message=f"视频生成服务 '{service_name}' 不存在"
        )
    
    try:
        # 获取任务结果
        result = await service.get_video_task_result(
            task_id=request.task_id,
            parameters=request.parameters
        )
        
        return normalize_response(result)
    except BusinessException as e:
        # 业务异常会被全局异常处理器捕获
        raise
    except Exception as e:
        # 其他异常转换为业务异常
        logger.error(f"获取视频生成任务结果失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"获取视频生成任务结果失败: {str(e)}",
            exception=e
        )


@router.get("/tasks", response_model=List[VideoTaskResultResponse])
async def list_video_tasks(
    skip: int = 0,
    limit: int = 20,
    service_name: str = None,
    status: str = None,
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取视频生成任务列表
    """
    try:
        # 获取任务列表
        tasks = task_service.list_tasks(
            service_type="video",
            service_name=service_name,
            status=status,
            skip=skip,
            limit=limit
        )
        
        # 转换为响应格式
        task_list = []
        for task in tasks:
            task_data = {
                "task_id": task.task_id,
                "status": task.status,
                "created_at": task.created_at,
                "service_name": task.service_name,
                "prompt": task.task_specific_data.get("prompt", "") if task.task_specific_data else "",
                "image_url": task.task_specific_data.get("image_url", "") if task.task_specific_data else "",
                "ratio": task.task_specific_data.get("ratio") if task.task_specific_data else None,
                "duration": task.task_specific_data.get("duration") if task.task_specific_data else None,
                "model": task.task_specific_data.get("model") if task.task_specific_data else None,
                "completed_at": task.completed_at,
                "videos": task.result.get("videos", []) if task.result else []
            }
            task_list.append(task_data)
        
        return normalize_response({"tasks": task_list, "total": len(task_list)})
    except BusinessException as e:
        # 业务异常会被全局异常处理器捕获
        raise
    except Exception as e:
        # 其他异常转换为业务异常
        logger.error(f"获取视频生成任务列表失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"获取视频生成任务列表失败: {str(e)}",
            exception=e
        )


@router.get("/services", response_model=VideoServicesListResponse)
async def list_video_services():
    """
    获取可用的视频生成服务列表
    """
    try:
        services = VideoServiceRegistry.list_services()
        return normalize_response({"services": services})
    except Exception as e:
        logger.error(f"获取视频生成服务列表失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"获取视频生成服务列表失败: {str(e)}",
            exception=e
        )
