"""
视频生成服务注册模块
"""
import logging
import os
from typing import Dict, Optional

from ai_services.video.base import VideoServiceBase
from db.service import TaskService

logger = logging.getLogger(__name__)

class VideoServiceRegistry:
    """视频生成服务注册表，用于管理所有视频生成服务提供商"""
    
    _services: Dict[str, VideoServiceBase] = {}
    
    @classmethod
    def register(cls, service: VideoServiceBase) -> None:
        """
        注册视频生成服务
        
        Args:
            service: 视频生成服务实例
        """
        cls._services[service.service_name] = service
        logger.info(f"已注册视频生成服务: {service.service_name}")
    
    @classmethod
    def get_service(cls, service_name: str) -> Optional[VideoServiceBase]:
        """
        获取视频生成服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            视频生成服务实例，如果不存在则返回None
        """
        return cls._services.get(service_name)
    
    @classmethod
    def list_services(cls) -> Dict[str, str]:
        """
        列出所有视频生成服务
        
        Returns:
            服务名称列表
        """
        return {name: service.__class__.__name__ for name, service in cls._services.items()}


def register_all_video_services(task_service: Optional[TaskService] = None) -> Dict[str, VideoServiceBase]:
    """
    注册所有视频生成服务
    
    从环境变量读取配置并注册服务
    
    Args:
        task_service: 任务服务实例，用于记录任务
        
    Returns:
        注册的服务实例字典，如果配置缺失则返回空字典
    """
    from ai_services.video.volcengine_video import register_volcengine_video_service
    
    registered_services = {}
    
    # 注册火山引擎视频生成服务
    volcengine_service = register_volcengine_video_service(task_service=task_service)
    if volcengine_service:
        registered_services[volcengine_service.service_name] = volcengine_service
    
    # 未来可以在这里添加其他视频生成服务的注册
    
    return registered_services
