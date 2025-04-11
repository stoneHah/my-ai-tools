"""
火山引擎(豆包)视频生成服务实现
"""
import json
import os
import time
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from volcenginesdkarkruntime import Ark

from ai_services.video.base import VideoServiceBase
from ai_services.video.registry import VideoServiceRegistry
from db.service import TaskService
from common.exceptions import BusinessException
from ai_services.storage.registry import get_storage_service
from common.utils import download_file_content

logger = logging.getLogger(__name__)

class VolcengineVideoService(VideoServiceBase):
    """火山引擎(豆包)视频生成服务"""
    
    def __init__(self, api_key: str, task_service: Optional[TaskService] = None):
        """
        初始化火山引擎视频服务
        
        Args:
            api_key: 火山引擎API密钥
            task_service: 任务服务，用于记录任务
        """
        self._api_key = api_key
        self._task_service = task_service
        self._client = Ark(api_key=api_key)
        self._default_model = "doubao-seaweed-241128"
        self._oss_provider = "aliyun"
        self._storage_service = get_storage_service(self._oss_provider)
        if not self._storage_service:
            raise Exception(f"找不到存储服务: {self._oss_provider}")
        
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "volcengine"
    
    async def create_image_to_video_task(self, 
                              prompt: str,
                              image_url: str,
                              ratio: Optional[str] = "9:16",
                              duration: Optional[int] = 5,
                              resolution: Optional[str] = "480p",
                              model: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """
        创建图生视频任务
        
        Args:
            prompt: 视频生成提示词
            image_url: 输入图片URL
            ratio: 视频宽高比，如"16:9"等，默认16:9
            duration: 视频时长(秒)，默认5秒
            resolution: 视频分辨率，默认480p
            model: 使用的模型名称
            **kwargs: 其他参数
            
        Returns:
            包含任务ID的响应
        """
        try:
            # 构建完整的提示词，包含比例和时长
            full_prompt = f"{prompt}  --ratio {ratio}  --dur {duration} --resolution {resolution}"

            model = model or self._default_model
            
            # 创建视频生成任务
            create_result = self._client.content_generation.tasks.create(
                model=model,
                content=[
                    {
                        # 文本提示词与参数组合
                        "type": "text",
                        "text": full_prompt
                    },
                    {
                        # 图片URL
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            )
            
            # 获取任务ID
            volcengine_task_id = create_result.id
            logger.info(f"Created image to video task: {volcengine_task_id}")
            
            # 记录任务
            if self._task_service:
                # 创建任务记录
                task = self._task_service.create_task(
                    service_type="video",
                    service_name=self.service_name,
                    status="pending",
                    parameters={
                        "prompt": prompt,
                        "image_url": image_url,
                        "ratio": ratio,
                        "duration": duration,
                        "resolution": resolution,
                        "model": model
                    },
                    task_specific_data={
                        "prompt": prompt,
                        "image_url": image_url,
                        "ratio": ratio,
                        "duration": duration,
                        "resolution": resolution,
                        "model": model,
                        "volcengine_task_id": volcengine_task_id
                    }
                )
                
                # 返回任务信息
                return {
                    "task_id": task.task_id,
                    "status": "pending",
                    "created_at": int(time.time()),
                    "prompt": prompt,
                    "image_url": image_url,
                    "ratio": ratio,
                    "duration": duration,
                    "resolution": resolution,
                    "model": model
                }
            else:
                # 如果没有任务服务，直接返回火山引擎的任务ID
                return {
                    "task_id": volcengine_task_id,
                    "status": "pending",
                    "created_at": int(time.time()),
                    "prompt": prompt,
                    "image_url": image_url,
                    "ratio": ratio,
                    "duration": duration,
                    "resolution": resolution,
                    "model": model
                }
                
        except Exception as e:
            logger.error(f"创建图生视频任务失败: {str(e)}", exc_info=True)
            raise BusinessException(
                code="VIDEO_TASK_CREATE_ERROR",
                message=f"创建图生视频任务失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def get_video_task_result(self,
                                  task_id: str,
                                  **kwargs) -> Dict[str, Any]:
        """
        获取视频生成任务结果
        
        Args:
            task_id: 任务ID
            **kwargs: 其他参数
            
        Returns:
            任务状态和结果，如果任务完成，则包含视频URL
        """
        try:
            # 如果有任务服务，先从数据库获取任务信息
            db_task = self._task_service.get_task(task_id)
            if not db_task:
                raise BusinessException(
                    code="TASK_NOT_FOUND",
                    message=f"任务不存在: {task_id}",
                    data={"task_id": task_id}
                )

            if db_task.status == "completed":
                # 确保completed_at是整数时间戳
                completed_at = None
                if db_task.completed_at:
                    if isinstance(db_task.completed_at, datetime):
                        completed_at = int(db_task.completed_at.timestamp())
                    else:
                        completed_at = int(db_task.completed_at)
                
                # 获取视频信息
                video_info = None
                if db_task.result and "video_url" in db_task.result:
                    video_info = {
                        "video_url": db_task.result.get("video_url"),
                        "object_key": db_task.result.get("object_key")
                    }
                
                return {
                    "task_id": task_id,
                    "status": db_task.status,
                    "created_at": int(db_task.created_at.timestamp()) if isinstance(db_task.created_at, datetime) else int(db_task.created_at),
                    "completed_at": completed_at,
                    "video_info": video_info
                }
            
            # 获取火山引擎任务ID
            volcengine_task_id = db_task.task_specific_data.get("volcengine_task_id")
            if not volcengine_task_id:
                raise BusinessException(
                    code="INVALID_TASK",
                    message=f"无效的任务: {task_id}，缺少火山引擎任务ID",
                    data={"task_id": task_id}
                )
            
            # 获取任务详情
            task_result = self._client.content_generation.tasks.get(task_id=volcengine_task_id)
            logger.info(f"获取任务详情: {task_result}")
            # 解析任务状态
            status = task_result.status
            
            # 映射火山引擎状态到我们的状态
            status_mapping = {
                "queued": "pending",
                "running": "running",
                "succeeded": "completed",
                "failed": "failed",
                "cancelled": "failed"
            }
            
            our_status = status_mapping.get(status, "pending")
            
            # 构建响应
            response = {
                "task_id": task_id,
                "status": our_status,
                "created_at": db_task.created_at
            }
            
            # 如果任务完成，添加结果
            if our_status == "completed":
                # 获取视频URL
                video_url = task_result.content.video_url
                
                # 将视频保存到OSS
                try:
                    # 生成OSS对象键名
                    object_key = f"videos/{int(time.time())}_{uuid.uuid4().hex}.mp4"
                    
                    # 将视频URL中的内容下载并上传到OSS
                    logger.info(f"开始将视频保存到OSS: {object_key}")
                    oss_url = await self._storage_service.upload_data(
                        data=await download_file_content(video_url),
                        object_key=object_key,
                        content_type="video/mp4"
                    )
                    logger.info(f"视频已保存到OSS: {oss_url}")
                    
                    video_info = {"video_url": oss_url, "object_key": object_key}
                    # 添加视频URL到响应
                    response["video_info"] = video_info
                    
                    # 更新数据库任务状态
                    if self._task_service:
                        self._task_service.update_task(
                            task_id=task_id,
                            status="completed",
                            result=video_info
                        )
                except Exception as e:
                    logger.error(f"保存视频到OSS失败: {str(e)}", exc_info=True)
                    raise BusinessException(
                        message=f"保存视频到OSS失败: {str(e)}",
                        data={"video_url": video_url}
                    )
            
            # 如果任务失败，添加错误信息
            elif our_status == "failed":
                error_message = task_result.failure_reason or "未知错误"
                response["error"] = error_message
                
                # 更新数据库任务状态
                if self._task_service:
                    self._task_service.update_task(
                        task_id=task_id,
                        status="failed",
                        error_message=error_message
                    )
            
            # 如果任务仍在进行中，更新数据库状态
            elif self._task_service:
                self._task_service.update_task(
                    task_id=task_id,
                    status=our_status
                )
            
            return response
            
        except BusinessException:
            # 直接抛出业务异常
            raise
        except Exception as e:
            logger.error(f"获取视频生成任务结果失败: {str(e)}", exc_info=True)
            raise BusinessException(
                code="VIDEO_TASK_RESULT_ERROR",
                message=f"获取视频生成任务结果失败: {str(e)}",
                data={"error": str(e)}
            )

    async def _download_video(self, video_url: str) -> bytes:
        """
        下载视频内容
        
        Args:
            video_url: 视频URL
            
        Returns:
            视频二进制数据
        """
        return await download_file_content(video_url)


def register_volcengine_video_service(task_service: Optional[TaskService] = None) -> Optional[VolcengineVideoService]:
    """
    注册火山引擎视频生成服务
    
    从环境变量读取配置并注册服务
    
    Args:
        task_service: 任务服务实例，用于记录任务
        
    Returns:
        注册的服务实例，如果配置缺失则返回None
    """
    # 从环境变量获取API密钥
    api_key = os.environ.get("ARK_API_KEY")
    
    if not api_key:
        logger.warning("未配置ARK_API_KEY环境变量，无法注册火山引擎视频生成服务")
        return None
    
    # 创建服务实例
    service = VolcengineVideoService(api_key=api_key, task_service=task_service)
    
    # 注册服务
    VideoServiceRegistry.register(service)
    
    return service
