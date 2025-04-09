"""
图像生成服务基础抽象类定义
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union


class ImageGenerationServiceBase(ABC):
    """图像生成服务抽象基类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    def service_type(self) -> str:
        """服务类型"""
        return "image"
    
    @abstractmethod
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
        """
        pass
    
    @abstractmethod
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
        """
        pass
