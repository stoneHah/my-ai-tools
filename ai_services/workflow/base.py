"""
工作流服务基类
定义了工作流服务的通用接口
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Union


class WorkflowServiceBase(ABC):
    """工作流服务抽象基类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
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
    
    async def chat(self, 
                 message: str,
                 conversation_id: Optional[str] = None,
                 **kwargs) -> Dict[str, Any]:
        """
        通过工作流提供聊天功能
        
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
    
    async def stream_chat(self, 
                        message: str,
                        conversation_id: Optional[str] = None,
                        **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        通过工作流提供流式聊天功能
        
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
            
    @abstractmethod
    async def create_conversation(self, **kwargs) -> str:
        """
        创建新的会话
        
        Args:
            **kwargs: 其他参数
            
        Returns:
            会话ID字符串
        """
        pass
