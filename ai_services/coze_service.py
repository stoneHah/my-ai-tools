"""
Coze AI服务实现
实现Coze智能体的接口
"""
import os
import datetime
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator

from cozepy import Coze, TokenAuth,ChatEventType, Message, MessageType

from ai_services.base import AIServiceBase, AIServiceRegistry

# 配置日志记录器
logger = logging.getLogger(__name__)

class CozeService(AIServiceBase):
    """Coze AI服务实现"""
    
    def __init__(self, api_token: str, api_base: Optional[str] = None, bot_id: Optional[str] = None):
        """
        初始化Coze服务
        
        Args:
            api_token: Coze API令牌
            api_base: Coze API基础URL，默认为None，使用SDK默认值
            bot_id: 默认机器人ID，如果不提供则需要在每次调用时指定
        """
        self.api_token = api_token
        self.api_base = api_base
        self.default_bot_id = bot_id
        
        # 创建异步Coze客户端
        self.client = Coze(
            auth=TokenAuth(api_token),
            base_url=api_base
        )
        
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "coze"

    @property
    def service_type(self) -> str:
        """服务类型"""
        return "chat"
    
    async def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        聊天接口
        
        Args:
            messages: 消息列表，每个消息包含role和content字段
            **kwargs: 其他参数
            
        Returns:
            聊天响应
        """
        # 提取最后一条用户消息
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            raise ValueError("消息列表中没有用户消息")
        
        last_user_message = user_messages[-1]["content"]
        
        # 调用现有的chat_completion方法
        return await self.chat_completion(
            message=last_user_message,
            conversation_id=kwargs.get("conversation_id"),
            **kwargs
        )
    
    async def stream_chat(self, messages: List[Dict[str, Any]], **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式聊天接口
        
        Args:
            messages: 消息列表，每个消息包含role和content字段
            **kwargs: 其他参数
            
        Yields:
            流式聊天响应
        """
        # 提取最后一条用户消息
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            raise ValueError("消息列表中没有用户消息")
        
        last_user_message = user_messages[-1]["content"]
        
        # 调用现有的stream_chat_completion方法
        async for chunk in self.stream_chat_completion(
            message=last_user_message,
            conversation_id=kwargs.get("conversation_id"),
            **kwargs
        ):
            yield chunk
    
    async def create_conversation(self, **kwargs) -> str:
        """
        创建新的会话
        
        Args:
            **kwargs: 其他参数
            
        Returns:
            会话ID字符串
        """
        
        # 仅返回会话ID字符串
        return self.client.conversations.create().id
    
    async def chat_completion(self, 
                            message: str,
                            conversation_id: Optional[str] = None,
                            **kwargs) -> Dict[str, Any]:
        """
        发送消息并获取回复（非流式）
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            **kwargs: 其他参数，可以包含bot_id等
            
        Returns:
            服务回复
        """
        bot_id = kwargs.get("bot_id", self.default_bot_id)
        if not bot_id:
            raise ValueError("未提供bot_id，请在参数中指定或在初始化服务时设置默认值")
        
        
        # 调用Coze API
        response = await self.client.chat.completions.create(
            bot_id=bot_id,
            messages=[{"role": "user", "content": message}],
            conversation_id=conversation_id
        )
        
        
        # 构建响应
        result = {
            "id": response.id,
            "message": response.choices[0].message.content,
            "role": "assistant"
        }
        
        # 如果有会话ID，则包含在响应中
        if conversation_id:
            result["conversation_id"] = conversation_id
        
        return result
    
    async def stream_chat_completion(self, 
                                   message: str,
                                   conversation_id: Optional[str] = None,
                                   **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式发送消息并获取回复
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            **kwargs: 其他参数，可以包含bot_id等
            
        Yields:
            流式回复的每个部分（标准字典格式，不是SSE格式）
        """
        # 获取机器人ID
        bot_id = kwargs.get('bot_id', self.default_bot_id)
        if not bot_id:
            raise ValueError("必须提供bot_id参数或在初始化时设置默认bot_id")
        
        try:
        
            # 正确处理流式响应
            for event in self.client.chat.stream(
                bot_id=bot_id,
                user_id="user", 
                additional_messages=[Message.build_user_question_text(message)],
                conversation_id=conversation_id
            ):
                print("------------event------------")
                print(event)
                if event.event == ChatEventType.CONVERSATION_MESSAGE_COMPLETED:
                    message = event.message
                    if message.type == MessageType.FUNCTION_CALL or message.type == MessageType.TOOL_OUTPUT or message.type == MessageType.TOOL_RESPONSE:
                        yield {
                            "content": message.content,
                            "role": message.role,
                            "type": message.type
                        }
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    message = event.message
                
                    # 构造返回的响应格式
                    yield {
                        "content": message.content,
                        "role": message.role,
                        "type": message.type
                    }

                if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                    pass
        except Exception as e:
            # 记录详细错误信息
            logger.error(f"流式聊天出错: {str(e)}", exc_info=True)
            raise
        


def register_coze_service() -> Optional[CozeService]:
    """
    注册Coze服务
    
    Returns:
        Coze服务实例，如果缺少必要的环境变量则返回None
    """
    api_token = os.getenv("COZE_API_TOKEN")
    if not api_token:
        return None
        
    api_base = os.getenv("COZE_API_BASE")
    default_bot_id = os.getenv("COZE_DEFAULT_BOT_ID")
    
    service = CozeService(
        api_token=api_token,
        api_base=api_base,
        bot_id=default_bot_id
    )
    
    AIServiceRegistry.register(service)
    return service
