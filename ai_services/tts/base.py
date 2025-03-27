"""
语音合成服务基础抽象类定义
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator, BinaryIO, Union


class TTSServiceBase(ABC):
    """语音合成服务基础抽象类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> str:
        """服务类型，应为tts"""
        pass
    
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        """
        将文本合成为语音
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数，如速度、音量、音调等
            
        Returns:
            合成的音频数据
        """
        pass
    
    @abstractmethod
    async def stream_synthesize(self, text: str, voice_id: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """
        流式将文本合成为语音
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数，如速度、音量、音调等
            
        Yields:
            流式合成的音频数据块
        """
        pass
    
    @abstractmethod
    async def save_to_file(self, text: str, voice_id: str, output_path: str, **kwargs) -> str:
        """
        将文本合成为语音并保存到文件
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            output_path: 输出文件路径
            **kwargs: 其他参数，如速度、音量、音调等
            
        Returns:
            保存的文件路径
        """
        pass
