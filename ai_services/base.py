"""
AI服务基础抽象接口
定义所有AI服务提供商必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Union


class AIServiceBase(ABC):
    """AI服务基础抽象类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> str:
        """服务类型，如chat、image、audio等"""
        pass
    
    @abstractmethod
    async def chat_completion(self, 
                             message: str, 
                             conversation_id: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """
        聊天完成接口
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            **kwargs: 其他参数
            
        Returns:
            完成结果
        """
        pass
    
    @abstractmethod
    async def stream_chat_completion(self, 
                                    message: str,
                                    conversation_id: Optional[str] = None,
                                    **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天完成接口
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            **kwargs: 其他参数
            
        Yields:
            流式完成结果
        """
        pass
    
    async def create_conversation(self, **kwargs) -> str:
        """
        创建新的会话
        
        Args:
            **kwargs: 其他参数
            
        Returns:
            会话ID字符串
        """
        raise NotImplementedError("此服务不支持创建会话")


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
    async def recognize(self, 
                       audio_url: Optional[str] = None,
                       audio_file_path: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        语音识别接口
        
        Args:
            audio_url: 音频文件URL，可选
            audio_file_path: 音频文件本地路径，可选（至少需要提供一个）
            **kwargs: 其他参数
            
        Returns:
            识别结果，包含以下字段：
            - id: 响应ID
            - text: 识别出的文本
            - status: 状态（success或error）
        """
        pass
    
    @abstractmethod
    async def stream_recognize(self, 
                              audio_url: Optional[str] = None,
                              audio_file_path: Optional[str] = None,
                              **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式语音识别接口
        
        Args:
            audio_url: 音频文件URL，可选
            audio_file_path: 音频文件本地路径，可选（至少需要提供一个）
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


class AIServiceRegistry:
    """AI服务注册表，用于管理所有AI服务提供商"""
    
    _services: Dict[str, Dict[str, Union[AIServiceBase, ASRServiceBase]]] = {}
    
    @classmethod
    def register(cls, service: Union[AIServiceBase, ASRServiceBase]) -> None:
        """
        注册AI服务
        
        Args:
            service: AI服务实例
        """
        service_name = service.service_name
        if service_name not in cls._services:
            cls._services[service_name] = {}
        
        cls._services[service_name][service.service_type] = service
    
    @classmethod
    def get_service(cls, service_name: str, service_type: str) -> Optional[Union[AIServiceBase, ASRServiceBase]]:
        """
        获取指定类型和名称的AI服务
        
        Args:
            service_name: 服务名称
            service_type: 服务类型
            
        Returns:
            AI服务实例，如果不存在则返回None
        """
        if service_name not in cls._services:
            return None
        
        return cls._services[service_name].get(service_type)
    
    @classmethod
    def list_services(cls, service_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        列出所有注册的AI服务
        
        Args:
            service_type: 可选的服务类型过滤
            
        Returns:
            按类型分组的服务名称列表
        """
        result = {}
        
        if service_type:
            if service_type in cls._services:
                result[service_type] = list(cls._services[service_type].keys())
        else:
            for type_name, services in cls._services.items():
                result[type_name] = list(services.keys())
        
        return result
