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
                             messages: List[Dict[str, Any]], 
                             **kwargs) -> Dict[str, Any]:
        """
        聊天完成接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            完成结果
        """
        pass
    
    @abstractmethod
    async def stream_chat_completion(self, 
                                    messages: List[Dict[str, Any]], 
                                    **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天完成接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            流式完成结果
        """
        pass


class AIServiceRegistry:
    """AI服务注册表，用于管理所有AI服务提供商"""
    
    _services: Dict[str, Dict[str, AIServiceBase]] = {}
    
    @classmethod
    def register(cls, service: AIServiceBase) -> None:
        """
        注册AI服务
        
        Args:
            service: AI服务实例
        """
        service_type = service.service_type
        if service_type not in cls._services:
            cls._services[service_type] = {}
        
        cls._services[service_type][service.service_name] = service
    
    @classmethod
    def get_service(cls, service_type: str, service_name: str) -> Optional[AIServiceBase]:
        """
        获取指定类型和名称的AI服务
        
        Args:
            service_type: 服务类型
            service_name: 服务名称
            
        Returns:
            AI服务实例，如果不存在则返回None
        """
        if service_type not in cls._services:
            return None
        
        return cls._services[service_type].get(service_name)
    
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
