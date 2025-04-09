"""
图像生成API路由
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from ai_services.base import AIServiceRegistry
from ai_services.image.base import ImageGenerationServiceBase
from api.image.models import (
    ImageGenerationRequest, 
    CreateImageTaskResponse,
    ImageTaskResultRequest,
    ImageTaskResultResponse,
    ImageServicesListResponse
)
from db.service import TaskService
from api.utils import get_task_service
from common.exceptions import BusinessException, ResourceNotFoundException, AIServiceError
from common.utils import normalize_response

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/image",
    tags=["image"],
    responses={404: {"description": "服务不存在"}}
)



@router.post("/task/create", response_model=CreateImageTaskResponse)
async def create_image_task(
    request: ImageGenerationRequest,
    task_service: TaskService = Depends(get_task_service)
):
    """
    创建图像生成任务
    
    根据提供的提示词创建图像生成任务，返回任务ID
    """
    service_name = request.service_name
    service = AIServiceRegistry.get_service(service_name, "image")
    
    if not service:
        raise ResourceNotFoundException(
            resource_type="图像生成服务",
            resource_id=service_name,
            message=f"图像生成服务 '{service_name}' 不存在"
        )
    
    try:
        # 创建任务
        task_dict = await service.create_image_task(
            prompt=request.prompt,
            aspect_ratio=request.aspect_ratio,
            model=request.model,
            num_images=request.num_images,
            parameters=request.parameters
        )
        
        # 从字典中获取数据
        return normalize_response({
            "task_id": task_dict["task_id"],
            "status": task_dict["status"],
            "created_at": task_dict["created_at"],
            "prompt": task_dict.get("prompt", request.prompt),
            "aspect_ratio": task_dict.get("aspect_ratio", request.aspect_ratio),
            "model": task_dict.get("model", request.model)
        })
    except BusinessException as e:
        # 业务异常会被全局异常处理器捕获
        raise
    except Exception as e:
        # 其他异常转换为业务异常
        logger.error(f"创建图像生成任务失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"创建图像生成任务失败: {str(e)}",
            exception=e
        )


@router.post("/task/result", response_model=ImageTaskResultResponse)
async def get_image_task_result(
    request: ImageTaskResultRequest,
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取图像生成任务结果
    
    根据任务ID获取图像生成任务的结果
    """
    task = task_service.get_task(request.task_id)
    if not task:
        raise ResourceNotFoundException(
            resource_type="任务",
            resource_id=request.task_id,
            message=f"任务 '{request.task_id}' 不存在"
        )
    
    service_name = task.service_name
    service = AIServiceRegistry.get_service(service_name, "image")
    
    if not service:
        raise ResourceNotFoundException(
            resource_type="图像生成服务",
            resource_id=service_name,
            message=f"图像生成服务 '{service_name}' 不存在"
        )
    
    try:
        # 获取任务结果
        result = await service.get_image_task_result(
            task_id=request.task_id,
            parameters=request.parameters
        )
        
        return normalize_response(result)
    except BusinessException as e:
        # 业务异常会被全局异常处理器捕获
        raise
    except Exception as e:
        # 其他异常转换为业务异常
        logger.error(f"获取图像生成任务结果失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"获取图像生成任务结果失败: {str(e)}",
            exception=e
        )


@router.get("/tasks", response_model=List[ImageTaskResultResponse])
async def list_image_tasks(
    skip: int = 0,
    limit: int = 20,
    service_name: str = None,
    status: str = None,
    task_service: TaskService = Depends(get_task_service)
):
    """
    获取图像生成任务列表
    """
    try:
        # 获取任务列表
        tasks = task_service.list_tasks(
            service_type="image",
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
                "aspect_ratio": task.task_specific_data.get("aspect_ratio") if task.task_specific_data else None,
                "model": task.task_specific_data.get("model") if task.task_specific_data else None,
                "completed_at": task.completed_at,
                "images": task.result.get("images", []) if task.result else []
            }
            task_list.append(task_data)
        
        return normalize_response({"tasks": task_list, "total": len(task_list)})
    except BusinessException as e:
        # 业务异常会被全局异常处理器捕获
        raise
    except Exception as e:
        # 其他异常转换为业务异常
        logger.error(f"获取图像生成任务列表失败: {str(e)}", exc_info=True)
        raise AIServiceError(
            message=f"获取图像生成任务列表失败: {str(e)}",
            exception=e
        )
