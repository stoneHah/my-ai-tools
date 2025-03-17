"""
Coze工作流服务实现
实现Coze工作流的接口
"""
import os
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

from cozepy import AsyncCoze, TokenAuth

from ai_services.base import AIServiceBase, AIServiceRegistry


class CozeWorkflowService(AIServiceBase):
    """Coze工作流服务实现"""
    
    def __init__(self, api_token: str, api_base: Optional[str] = None, workflow_id: Optional[str] = None):
        """
        初始化Coze工作流服务
        
        Args:
            api_token: Coze API访问令牌
            api_base: Coze API基础URL，默认为None（使用SDK默认值）
            workflow_id: 默认使用的工作流ID
        """
        self.api_token = api_token
        self.api_base = api_base
        self.default_workflow_id = workflow_id
        
        # 创建异步客户端
        self.client = AsyncCoze(
            auth=TokenAuth(api_token),
            base_url=api_base
        )
    
    @property
    def service_name(self) -> str:
        return "coze_workflow"
    
    @property
    def service_type(self) -> str:
        return "workflow"
    
    async def chat_completion(self, 
                             messages: List[Dict[str, Any]], 
                             **kwargs) -> Dict[str, Any]:
        """
        运行工作流（非流式）
        
        Args:
            messages: 消息列表，第一条消息的内容将作为工作流输入
            **kwargs: 其他参数，包括workflow_id
            
        Returns:
            工作流运行结果
        """
        workflow_id = kwargs.get("workflow_id", self.default_workflow_id)
        if not workflow_id:
            raise ValueError("workflow_id必须在参数中提供或在初始化时设置")
        
        # 获取第一条用户消息作为工作流输入
        user_input = ""
        for message in messages:
            if message.get("role") == "user":
                user_input = message.get("content", "")
                break
        
        if not user_input:
            user_input = messages[0].get("content", "") if messages else ""
        
        # 运行工作流
        response = await self.client.workflows.runs.create(
            workflow_id=workflow_id,
            input=user_input,
            stream=False
        )
        
        # 将工作流响应转换为与聊天完成兼容的格式
        result = response.model_dump()
        
        # 添加兼容聊天完成的字段
        if "choices" not in result:
            result["choices"] = [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.get("output", "")
                },
                "finish_reason": "stop"
            }]
        
        return result
    
    async def stream_chat_completion(self, 
                                   messages: List[Dict[str, Any]], 
                                   **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行工作流
        
        Args:
            messages: 消息列表，第一条消息的内容将作为工作流输入
            **kwargs: 其他参数，包括workflow_id
            
        Yields:
            流式工作流运行结果
        """
        workflow_id = kwargs.get("workflow_id", self.default_workflow_id)
        if not workflow_id:
            raise ValueError("workflow_id必须在参数中提供或在初始化时设置")
        
        # 获取第一条用户消息作为工作流输入
        user_input = ""
        for message in messages:
            if message.get("role") == "user":
                user_input = message.get("content", "")
                break
        
        if not user_input:
            user_input = messages[0].get("content", "") if messages else ""
        
        # 流式运行工作流
        stream = await self.client.workflows.runs.create(
            workflow_id=workflow_id,
            input=user_input,
            stream=True
        )
        
        # 处理流式响应
        async for chunk in stream:
            # 将工作流块转换为与聊天完成兼容的格式
            result = chunk.model_dump()
            
            # 添加兼容聊天完成的字段
            if "choices" not in result:
                result["choices"] = [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": result.get("delta", {}).get("output", "")
                    }
                }]
            
            yield result


# 自动注册服务
def register_coze_workflow_service():
    """从环境变量获取配置并注册Coze工作流服务"""
    api_token = os.getenv("COZE_API_TOKEN")
    api_base = os.getenv("COZE_API_BASE")
    default_workflow_id = os.getenv("COZE_DEFAULT_WORKFLOW_ID")
    
    if api_token:
        service = CozeWorkflowService(
            api_token=api_token,
            api_base=api_base,
            workflow_id=default_workflow_id
        )
        AIServiceRegistry.register(service)
        return service
    
    return None
