"""
语音识别服务基础抽象类定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator


class ASRServiceBase(ABC):
    """语音识别服务基础抽象类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> str:
        """服务类型，应为asr"""
        pass
    
    @abstractmethod
    async def recognize_url(self, audio_url: str, **kwargs) -> Dict[str, Any]:
        """
        通过URL进行语音识别
        
        Args:
            audio_url: 音频URL
            **kwargs: 其他参数
            
        Returns:
            识别结果，包含以下字段：
            - id: 响应ID
            - text: 识别出的文本
            - status: 状态（success或error）
        """
        pass
    
    @abstractmethod
    async def recognize_file(self, audio_file_path: str, **kwargs) -> Dict[str, Any]:
        """
        通过本地文件进行语音识别
        
        Args:
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Returns:
            识别结果，包含以下字段：
            - id: 响应ID
            - text: 识别出的文本
            - status: 状态（success或error）
        """
        pass
    
    
    @abstractmethod
    async def stream_recognize_url(self, audio_url: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        通过URL进行流式语音识别
        
        Args:
            audio_url: 音频URL
            **kwargs: 其他参数
            
        Yields:
            流式识别结果，每个块包含以下字段：
            - id: 响应ID
            - text: 当前累积的文本
            - delta: 本次增量内容
            - status: 状态（success或error）
            - is_final: 是否为最终结果
        """
        pass
    
    @abstractmethod
    async def stream_recognize_file(self, audio_file_path: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        通过本地文件进行流式语音识别
        
        Args:
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Yields:
            流式识别结果，每个块包含以下字段：
            - id: 响应ID
            - text: 当前累积的文本
            - delta: 本次增量内容
            - status: 状态（success或error）
            - is_final: 是否为最终结果
        """
        pass
    
