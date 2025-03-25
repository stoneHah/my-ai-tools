"""
Coze工作流服务
实现基于Coze工作流的服务
"""
import os
import datetime
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from abc import abstractmethod

from cozepy import AsyncCoze, TokenAuth,WorkflowEventType  

from ai_services.base import AIServiceBase, AIServiceRegistry


class WorkflowServiceBase(AIServiceBase):
    """工作流服务抽象基类"""
    
    @property
    def service_type(self) -> str:
        """服务类型"""
        return "workflow"
    
    @abstractmethod
    async def run_workflow(self, 
                         workflow_id: str,
                         input_params: Dict[str, Any],
                         **kwargs) -> Dict[str, Any]:
        """
        运行工作流并获取结果
        
        Args:
            workflow_id: 工作流ID
            input_params: 工作流输入参数，字典类型
            **kwargs: 其他参数
            
        Returns:
            工作流运行结果
        """
        pass
    
    @abstractmethod
    async def stream_workflow(self, 
                            workflow_id: str,
                            input_params: Dict[str, Any],
                            **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行工作流并获取结果
        
        Args:
            workflow_id: 工作流ID
            input_params: 工作流输入参数，字典类型
            **kwargs: 其他参数
            
        Yields:
            流式工作流运行结果的每个部分
        """
        pass
    
    async def chat_completion(self, 
                             message: str,
                             conversation_id: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """
        实现AIServiceBase的抽象方法，通过工作流提供聊天功能
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            **kwargs: 其他参数，可以包含workflow_id等
            
        Returns:
            工作流运行结果
        """
        workflow_id = kwargs.get("workflow_id", getattr(self, "default_workflow_id", None))
        if not workflow_id:
            raise ValueError("未提供workflow_id，请在参数中指定或在初始化服务时设置默认值")
        
        # 准备输入参数
        input_params = {"input": message}
        if kwargs.get("input_params"):
            # 如果提供了额外的输入参数，合并它们
            input_params.update(kwargs["input_params"])
        
        # 调用工作流
        result = await self.run_workflow(
            workflow_id=workflow_id,
            input_params=input_params,
            **kwargs
        )
        
        return result
    
    async def stream_chat_completion(self, 
                                    message: str,
                                    conversation_id: Optional[str] = None,
                                    **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        实现AIServiceBase的抽象方法，通过工作流提供流式聊天功能
        
        Args:
            message: 用户消息
            conversation_id: 会话ID
            **kwargs: 其他参数，可以包含workflow_id等
            
        Yields:
            流式工作流运行结果的每个部分
        """
        workflow_id = kwargs.get("workflow_id", getattr(self, "default_workflow_id", None))
        if not workflow_id:
            raise ValueError("未提供workflow_id，请在参数中指定或在初始化服务时设置默认值")
        
        # 准备输入参数
        input_params = {"input": message}
        if kwargs.get("input_params"):
            # 如果提供了额外的输入参数，合并它们
            input_params.update(kwargs["input_params"])
        
        # 调用流式工作流
        async for chunk in self.stream_workflow(
            workflow_id=workflow_id,
            input_params=input_params,
            **kwargs
        ):
            yield chunk


class CozeWorkflowService(WorkflowServiceBase):
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
    
    async def run_workflow(self, 
                         workflow_id: str,
                         input_params: Dict[str, Any],
                         **kwargs) -> Dict[str, Any]:
        """
        运行工作流并获取结果
        
        Args:
            workflow_id: 工作流ID
            input_params: 工作流输入参数，字典类型
            **kwargs: 其他参数
            
        Returns:
            工作流运行结果
        """
        # 调用Coze工作流API
        response = await self.client.workflows.runs.create(
            workflow_id=workflow_id,
            parameters=input_params
        )
        
        # 返回工作流运行结果
        return json.loads(response.data)
    
    async def stream_workflow(self, 
                            workflow_id: str,
                            input_params: Dict[str, Any],
                            **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行工作流并获取结果
        
        Args:
            workflow_id: 工作流ID
            input_params: 工作流输入参数，字典类型
            **kwargs: 其他参数
            
        Yields:
            流式工作流运行结果的每个部分
        """
        # 处理可能存在的会话ID
        conversation_id = kwargs.get("conversation_id")
        
        # 调用Coze工作流API进行流式响应
        stream = await self.client.workflows.runs.create(
            workflow_id=workflow_id,
            parameters=input_params,
            stream=True
        )
        
        response_id = None
        full_content = ""
        
        async for event in stream:
            # 提取运行ID
            if hasattr(event, 'run_id') and not response_id:
                response_id = event.run_id
                
            # 提取会话ID（如果存在）
            conv_id = None
            if hasattr(event, 'conversation_id') and event.conversation_id:
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
                elif conversation_id:
                    result["conversation_id"] = conversation_id
                
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
