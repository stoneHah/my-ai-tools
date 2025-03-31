"""
语音克隆服务基类
定义了语音克隆服务的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class VoiceCloneServiceBase(ABC):
    """语音克隆服务基类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> str:
        """服务类型，应为voice-clone"""
        pass
    
    @abstractmethod
    async def create_clone_voice(self, sample_url: str, voice_name: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        创建克隆音色
        
        Args:
            sample_url: 样本音频URL
            voice_name: 音色名称
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            克隆任务信息，包含task_id、status等
        """
        pass
    
    @abstractmethod
    async def query_clone_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        查询克隆任务状态
        
        Args:
            task_id: 任务ID
            **kwargs: 其他参数
            
        Returns:
            任务状态信息，包含status、voice_id等
        """
        pass
    
    @abstractmethod
    async def list_clone_voices(self, user_id: str, app_id: str, **kwargs) -> List[Dict[str, Any]]:
        """
        获取用户的克隆音色列表
        
        Args:
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            克隆音色列表
        """
        pass
    
    @abstractmethod
    async def delete_clone_voice(self, voice_id: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        删除克隆音色
        
        Args:
            voice_id: 音色ID
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            删除结果
        """
        pass
    
    @abstractmethod
    async def update_clone_voice(self, voice_id: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新克隆音色信息
        
        Args:
            voice_id: 音色ID
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数，如name、description等
            
        Returns:
            更新结果
        """
        pass
