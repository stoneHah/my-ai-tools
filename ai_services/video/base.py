"""
视频生成服务基础抽象类定义
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class VideoServiceBase(ABC):
    """视频生成服务抽象基类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    def service_type(self) -> str:
        """服务类型"""
        return "video"
    
    @abstractmethod
    async def create_image_to_video_task(self, 
                              prompt: str,
                              image_url: str,
                              ratio: Optional[str] = None,
                              duration: Optional[int] = None,
                              resolution: Optional[str] = None,
                              model: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """
        创建图生视频任务
        
        Args:
            prompt: 视频生成提示词
            image_url: 输入图片URL
            ratio: 视频宽高比，如"16:9"等
            duration: 视频时长(秒)
            model: 使用的模型名称
            **kwargs: 其他参数
            
        Returns:
            包含任务ID的响应
        """
        pass
    
    @abstractmethod
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
        pass
