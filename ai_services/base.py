"""
AI服务基础抽象类定义
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, AsyncGenerator

logger = logging.getLogger(__name__)

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
        """服务类型，如chat、image等"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        聊天接口
        
        Args:
            messages: 消息列表，每个消息包含role和content字段
            **kwargs: 其他参数
            
        Returns:
            聊天响应
        """
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天接口
        
        Args:
            messages: 消息列表，每个消息包含role和content字段
            **kwargs: 其他参数
            
        Yields:
            流式聊天响应
        """
        pass
    
    @abstractmethod
    async def create_conversation(self, **kwargs) -> str:
        """
        创建会话
        
        Args:
            **kwargs: 会话参数
            
        Returns:
            会话ID字符串
        """
        raise NotImplementedError("此服务不支持创建会话")


class AIServiceRegistry:
    """AI服务注册表，用于管理所有AI服务提供商"""
    
    _services: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, service: Any) -> None:
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
    def get_service(cls, service_name: str, service_type: str) -> Optional[Any]:
        """
        获取AI服务
        
        Args:
            service_name: 服务名称
            service_type: 服务类型
            
        Returns:
            AI服务实例，如果不存在则返回None
        """
        if service_type not in cls._services:
            return None
        
        return cls._services[service_type].get(service_name)
    
    @classmethod
    def list_services(cls, service_type: Optional[str] = None) -> Dict[str, List[str]]:
        """
        列出所有AI服务
        
        Args:
            service_type: 服务类型，如果不指定则列出所有类型
            
        Returns:
            服务列表，按类型分组
        """
        result = {}
        
        if service_type:
            # 只列出指定类型的服务
            if service_type in cls._services:
                result[service_type] = list(cls._services[service_type].keys())
        else:
            # 列出所有类型的服务
            for type_name, services in cls._services.items():
                result[type_name] = list(services.keys())
        
        return result
