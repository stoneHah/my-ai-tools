"""
Coze工作流服务
实现基于Coze工作流的服务
"""
import os
import datetime
import json
from typing import Dict, List, Any, Optional, AsyncGenerator

from cozepy import AsyncCoze, TokenAuth,WorkflowEventType  

from ai_services.base import AIServiceBase, AIServiceRegistry


class CozeWorkflowService(AIServiceBase):
    """Coze工作流服务"""
    
    def __init__(self, api_token: str, api_base: Optional[str] = None, workflow_id: Optional[str] = None):
        """
        初始化Coze工作流服务
        
        Args:
            api_token: Coze API令牌
            api_base: Coze API基础URL，默认为None，使用SDK默认值
            workflow_id: 默认工作流ID，如果不提供则需要在每次调用时指定
        """
        self.api_token = api_token
        self.api_base = api_base
        self.default_workflow_id = workflow_id
        
        # 创建异步Coze客户端
        self.client = AsyncCoze(
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
        return "workflow"
    
    async def create_conversation(self, **kwargs) -> str:
        """
        创建新的会话
        
        Args:
            **kwargs: 其他参数
            
        Returns:
            会话ID字符串
        """
        # 工作流API没有显式创建会话的接口，执行工作流时会自动创建
        # 返回一个临时ID，实际会话将在首次调用工作流时创建
        return f"wf_temp_{datetime.datetime.now().timestamp()}"
    
    async def chat_completion(self, 
                             message: str,
                             conversation_id: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """
        运行工作流并获取结果
        
        Args:
            message: 工作流输入
            conversation_id: 会话ID
            **kwargs: 其他参数，可以包含workflow_id等
            
        Returns:
            工作流运行结果
        """
        workflow_id = kwargs.get("workflow_id", self.default_workflow_id)
        if not workflow_id:
            raise ValueError("未提供workflow_id，请在参数中指定或在初始化服务时设置默认值")
        
        # 调用Coze工作流API
        response = await self.client.workflows.run(
            workflow_id=workflow_id,
            input=message,
            conversation_id=conversation_id
        )
        
        # 构建响应
        result = {
            "id": response.run_id,
            "message": response.output,
            "role": "assistant"
        }
        
        # 如果有会话ID，则包含在响应中
        if conversation_id:
            result["conversation_id"] = conversation_id
        elif hasattr(response, 'conversation_id') and response.conversation_id:
            # 如果没有提供会话ID但响应中包含会话ID
            result["conversation_id"] = response.conversation_id
        
        return result
    
    async def stream_chat_completion(self, 
                                    message: str,
                                    conversation_id: Optional[str] = None,
                                    **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行工作流并获取结果
        
        Args:
            message: 工作流输入
            conversation_id: 会话ID
            **kwargs: 其他参数，可以包含workflow_id等
            
        Yields:
            流式工作流运行结果的每个部分（标准字典格式，不是SSE格式）
        """
        workflow_id = kwargs.get("workflow_id", self.default_workflow_id)
        if not workflow_id:
            raise ValueError("未提供workflow_id，请在参数中指定或在初始化服务时设置默认值")
        
        # 调用Coze工作流API进行流式响应
        stream = await self.client.workflows.run(
            workflow_id=workflow_id,
            input=message,
            conversation_id=conversation_id,
            stream=True
        )
        
        response_id = None
        full_content = ""
        conv_id = conversation_id
        
        async for event in stream:
            # 提取运行ID
            if hasattr(event, 'run_id') and not response_id:
                response_id = event.run_id
                
            # 提取会话ID（如果存在）
            if hasattr(event, 'conversation_id') and event.conversation_id and not conv_id:
                conv_id = event.conversation_id
                
            # 处理增量输出
            if event.event == WorkflowEventType.OUTPUT_DELTA and event.delta:
                full_content += event.delta
                result = {
                    "id": response_id or "",
                    "delta": event.delta,
                    "content": full_content,
                    "role": "assistant"
                }
                
                # 如果有会话ID，则包含在响应中
                if conv_id:
                    result["conversation_id"] = conv_id
                
                yield result


def register_coze_workflow_service() -> Optional[CozeWorkflowService]:
    """
    注册Coze工作流服务
    
    从环境变量读取配置并注册服务
    
    Returns:
        注册的服务实例，如果配置缺失则返回None
    """
    api_token = os.getenv("COZE_API_TOKEN")
    api_base = os.getenv("COZE_API_BASE")
    workflow_id = os.getenv("COZE_DEFAULT_WORKFLOW_ID")
    
    if not api_token:
        print("COZE_API_TOKEN环境变量未设置，无法注册Coze工作流服务")
        return None
    
    # 创建并注册服务
    service = CozeWorkflowService(
        api_token=api_token,
        api_base=api_base,
        workflow_id=workflow_id
    )
    AIServiceRegistry.register(service)
    
    return service
