"""
Coze AI服务实现
实现Coze智能体的接口
"""
import os
from typing import Dict, List, Any, Optional, AsyncGenerator

from cozepy import AsyncCoze, TokenAuth

from ai_services.base import AIServiceBase, AIServiceRegistry


class CozeService(AIServiceBase):
    """Coze AI服务实现"""
    
    def __init__(self, api_token: str, api_base: Optional[str] = None, bot_id: Optional[str] = None):
        """
        初始化Coze服务
        
        Args:
            api_token: Coze API访问令牌
            api_base: Coze API基础URL，默认为None（使用SDK默认值）
            bot_id: 默认使用的Bot ID
        """
        self.api_token = api_token
        self.api_base = api_base
        self.default_bot_id = bot_id
        
        # 创建异步客户端
        self.client = AsyncCoze(
            auth=TokenAuth(api_token),
            base_url=api_base
        )
    
    @property
    def service_name(self) -> str:
        return "coze"
    
    @property
    def service_type(self) -> str:
        return "chat"
    
    async def chat_completion(self, 
                             messages: List[Dict[str, Any]], 
                             **kwargs) -> Dict[str, Any]:
        """
        聊天完成接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数，包括bot_id
            
        Returns:
            完成结果
        """
        bot_id = kwargs.get("bot_id", self.default_bot_id)
        if not bot_id:
            raise ValueError("bot_id必须在参数中提供或在初始化时设置")
        
        response = await self.client.chat.completions.create(
            bot_id=bot_id,
            messages=messages,
            stream=False
        )
        
        return response.model_dump()
    
    async def stream_chat_completion(self, 
                                   messages: List[Dict[str, Any]], 
                                   **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天完成接口
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数，包括bot_id
            
        Yields:
            流式完成结果
        """
        bot_id = kwargs.get("bot_id", self.default_bot_id)
        if not bot_id:
            raise ValueError("bot_id必须在参数中提供或在初始化时设置")
        
        stream = await self.client.chat.completions.create(
            bot_id=bot_id,
            messages=messages,
            stream=True
        )
        
        async for chunk in stream:
            yield chunk.model_dump()


# 自动注册服务
def register_coze_service():
    """从环境变量获取配置并注册Coze服务"""
    api_token = os.getenv("COZE_API_TOKEN")
    api_base = os.getenv("COZE_API_BASE")
    default_bot_id = os.getenv("COZE_DEFAULT_BOT_ID")
    
    if api_token:
        service = CozeService(
            api_token=api_token,
            api_base=api_base,
            bot_id=default_bot_id
        )
        AIServiceRegistry.register(service)
        return service
    
    return None
