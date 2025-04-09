"""
基于Coze工作流的图像生成服务
"""
import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator

from fastapi import Depends
from cozepy import AsyncCoze, TokenAuth, WorkflowExecuteStatus

from ai_services.base import AIServiceRegistry
from ai_services.image.base import ImageGenerationServiceBase
from db.service import TaskService
from common.exceptions import (
    BusinessException, 
    InvalidParameterException, 
    ServiceUnavailableException,
    TaskFailedException,
    ResourceNotFoundException
)

logger = logging.getLogger(__name__)

class CozeImageService(ImageGenerationServiceBase):
    """基于Coze工作流的图像生成服务"""
    
    def __init__(self, 
                api_token: str, 
                api_base: Optional[str] = None, 
                workflow_id: Optional[str] = None,
                poll_interval: int = 1,
                timeout: int = 300,
                task_service: Optional[TaskService] = None):
        """
        初始化Coze图像生成服务
        
        Args:
            api_token: Coze API令牌
            api_base: Coze API基础URL，默认为None，使用SDK默认值
            workflow_id: 默认工作流ID，如果不提供则需要在每次调用时指定
            poll_interval: 轮询间隔（秒）
            timeout: 超时时间（秒）
            task_service: 任务服务实例，用于记录任务
        """
        self.api_token = api_token
        self.api_base = api_base
        self.default_workflow_id = workflow_id
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.task_service = task_service
        
        # 创建异步Coze客户端
        self.client = AsyncCoze(
            auth=TokenAuth(api_token),
            base_url=api_base
        )
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "coze"
    
    async def create_image_task(self, 
                              prompt: str,
                              aspect_ratio: Optional[str] = None,
                              model: Optional[str] = None,
                              num_images: Optional[int] = 1,
                              **kwargs) -> Dict[str, Any]:
        """
        创建图像生成任务
        
        Args:
            prompt: 图像生成提示词
            aspect_ratio: 图像宽高比，如"1:1", "16:9"等
            model: 使用的模型名称
            num_images: 生成图像的数量，默认为1
            **kwargs: 其他参数
            
        Returns:
            包含任务ID的响应
            
        Raises:
            InvalidParameterException: 参数无效
            ServiceUnavailableException: 服务不可用
        """
        workflow_id = kwargs.get("workflow_id", self.default_workflow_id)
        if not workflow_id:
            raise InvalidParameterException(
                parameter="workflow_id",
                reason="未提供workflow_id，请在参数中指定或在初始化服务时设置默认值"
            )
        
        # 准备输入参数
        input_params = {
            "prompt": prompt
        }
        
        # 添加可选参数
        if aspect_ratio:
            input_params["aspect_ratio"] = aspect_ratio
        if model:
            input_params["model"] = model
        if num_images:
            input_params["num_images"] = num_images
            
        # 合并其他参数
        if kwargs.get("input_params"):
            input_params.update(kwargs["input_params"])
        
        # 调用Coze工作流API创建异步工作流运行
        try:
            workflow_run = await self.client.workflows.runs.create(
                workflow_id=workflow_id,
                parameters=input_params,
                is_async=True
            )
        except Exception as e:
            logger.error(f"创建Coze工作流运行失败: {str(e)}", exc_info=True)
            raise ServiceUnavailableException(
                service_name=self.service_name,
                reason=f"无法创建图像生成任务: {str(e)}",
                details={"workflow_id": workflow_id}
            )
        
        execute_id = workflow_run.execute_id
        logger.info(f"已创建图像生成任务: {execute_id}")
        
        # 记录任务到数据库
        task_id = execute_id
        if self.task_service:
            try:
                # 创建任务特有数据
                task_specific_data = {
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "model": model,
                    "num_images": num_images,
                    "workflow_id": workflow_id,
                    "execute_id": execute_id
                }
                
                task = self.task_service.create_task(
                    service_type="image",
                    service_name=self.service_name,
                    status="pending",
                    parameters=input_params,
                    task_specific_data=task_specific_data
                )
                # 使用数据库生成的任务ID
                task_id = task.task_id
                logger.info(f"已记录图像生成任务到数据库: {task_id}")
            except Exception as e:
                logger.error(f"记录任务到数据库失败: {str(e)}", exc_info=True)
                # 这里不抛出异常，因为任务已经创建成功，只是记录失败
        
        # 返回任务信息
        return {
            "task_id": task_id,
            "status": "pending",
            "created_at": time.time(),
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "model": model,
            "num_images": num_images
        }
    
    async def get_image_task_result(self,
                                  task_id: str,
                                  **kwargs) -> Dict[str, Any]:
        """
        获取图像生成任务结果
        
        Args:
            task_id: 任务ID
            **kwargs: 其他参数
            
        Returns:
            任务状态和结果，如果任务完成，则包含图像URL
            
        Raises:
            ResourceNotFoundException: 任务不存在
            ServiceUnavailableException: 服务不可用
            TaskFailedException: 任务执行失败
        """
        workflow_id = kwargs.get("workflow_id", self.default_workflow_id)
        if not workflow_id:
            raise InvalidParameterException(
                parameter="workflow_id",
                reason="未提供workflow_id，请在参数中指定或在初始化服务时设置默认值"
            )
        
        # 首先检查数据库中的任务状态
        execute_id = task_id  # 默认使用task_id作为execute_id
        if self.task_service:
            try:
                task = self.task_service.get_task(task_id)
                if not task:
                    raise ResourceNotFoundException(
                        resource_type="Task",
                        resource_id=task_id
                    )
                
                # 如果任务存在于数据库中，获取execute_id
                if task.task_specific_data and "execute_id" in task.task_specific_data:
                    execute_id = task.task_specific_data["execute_id"]
                
                if task.status == "completed":
                    # 如果任务已完成，直接返回结果
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "images": task.result.get("images", []) if task.result else [],
                        "completed_at": task.completed_at.timestamp() if task.completed_at else None
                    }
                elif task.status in ["failed", "error"]:
                    # 如果任务已失败，抛出业务异常
                    raise TaskFailedException(
                        task_id=task_id,
                        reason=task.error_message or "未知错误",
                        details={"service_name": self.service_name}
                    )
            except ResourceNotFoundException:
                # 直接向上抛出资源未找到异常
                raise
            except BusinessException:
                # 直接向上抛出业务异常
                raise
            except Exception as e:
                logger.error(f"从数据库获取任务状态失败: {str(e)}", exc_info=True)
                # 这里不抛出异常，继续尝试从Coze API获取任务状态
        
        # 获取运行历史
        try:
            run_history = await self.client.workflows.runs.run_histories.retrieve(
                workflow_id=workflow_id,
                execute_id=execute_id
            )
        except Exception as e:
            error_msg = f"获取任务状态失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 更新数据库中的任务状态
            if self.task_service:
                try:
                    self.task_service.update_task_status(
                        task_id=task_id,
                        status="error",
                        error_message=error_msg
                    )
                except Exception as db_error:
                    logger.error(f"更新任务状态到数据库失败: {str(db_error)}", exc_info=True)
            
            raise ServiceUnavailableException(
                service_name=self.service_name,
                reason=error_msg,
                details={"task_id": task_id, "execute_id": execute_id}
            )
        
        # 检查运行状态
        if run_history.execute_status == WorkflowExecuteStatus.FAIL:
            error_message = run_history.error_message or "未知错误"
            logger.error(f"图像生成任务失败: {error_message}")
            
            # 更新数据库中的任务状态
            if self.task_service:
                try:
                    self.task_service.update_task_status(
                        task_id=task_id,
                        status="failed",
                        error_message=error_message
                    )
                except Exception as e:
                    logger.error(f"更新任务状态到数据库失败: {str(e)}", exc_info=True)
            
            raise TaskFailedException(
                task_id=task_id,
                reason=error_message,
                details={"service_name": self.service_name}
            )
        
        elif run_history.execute_status == WorkflowExecuteStatus.RUNNING:
            # 任务仍在运行
            # 更新数据库中的任务状态
            if self.task_service:
                try:
                    self.task_service.update_task_status(
                        task_id=task_id,
                        status="running"
                    )
                except Exception as e:
                    logger.error(f"更新任务状态到数据库失败: {str(e)}", exc_info=True)
            
            return {
                "task_id": task_id,
                "status": "running"
            }
        
        elif run_history.execute_status == WorkflowExecuteStatus.SUCCESS:
            # 任务完成，解析结果
            output = run_history.output
            logger.info(f"图像生成任务已完成： {output}")
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，保持原样
                    output = {"raw_output": output}
            
            data = json.loads(output["Output"])["data"] if isinstance(output, dict) and "Output" in output else ""
            
            # 处理图像URL列表
            image_urls = []
            if isinstance(data, list):
                # 如果data已经是列表，直接使用
                image_urls = data
            elif data:
                # 如果data是单个URL，放入列表
                image_urls = [data]
                
            result = {
                "images": image_urls
            }
            
            # 更新数据库中的任务状态
            if self.task_service:
                try:
                    self.task_service.update_task_status(
                        task_id=task_id,
                        status="completed",
                        result=result
                    )
                except Exception as e:
                    logger.error(f"更新任务状态到数据库失败: {str(e)}", exc_info=True)
            
            return {
                "task_id": task_id,
                "status": "completed",
                "images": image_urls,
                "completed_at": int(time.time())
            }
        
        else:
            # 未知状态
            return {
                "task_id": task_id,
                "status": "unknown",
                "raw_status": run_history.execute_status
            }


def register_coze_image_service(task_service: Optional[TaskService] = None) -> Optional[CozeImageService]:
    """
    注册Coze图像生成服务
    
    从环境变量读取配置并注册服务
    
    Args:
        task_service: 任务服务实例，用于记录任务
        
    Returns:
        注册的服务实例，如果配置缺失则返回None
    """
    api_token = os.getenv("COZE_API_TOKEN")
    api_base = os.getenv("COZE_API_BASE")
    workflow_id = os.getenv("COZE_IMAGE_WORKFLOW_ID")
    
    if not api_token:
        logger.warning("COZE_API_TOKEN环境变量未设置，无法注册Coze图像生成服务")
        return None
    
    if not workflow_id:
        logger.warning("COZE_IMAGE_WORKFLOW_ID环境变量未设置，无法注册Coze图像生成服务")
        return None
    
    # 创建并注册服务
    service = CozeImageService(
        api_token=api_token,
        api_base=api_base,
        workflow_id=workflow_id,
        task_service=task_service
    )
    AIServiceRegistry.register(service)
    
    logger.info(f"已注册Coze图像生成服务，工作流ID: {workflow_id}")
    return service
