"""
Coze工作流服务
实现基于Coze工作流的服务
"""
import os
import datetime
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

from cozepy import AsyncCoze, TokenAuth, WorkflowEventType

from ai_services.base import AIServiceRegistry
from ai_services.workflow.base import WorkflowServiceBase


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
        # 调用Coze工作流API，获取流式响应
        async for event in self.client.workflows.runs.stream(
            workflow_id=workflow_id,
            parameters=input_params
        ):
            # 根据事件类型处理不同的响应
            if event.type == WorkflowEventType.WORKFLOW_RUN_STEP_DELTA:
                # 工作流步骤增量更新
                data = json.loads(event.data) if isinstance(event.data, str) else event.data
                yield {
                    "type": "delta",
                    "data": data
                }
            elif event.type == WorkflowEventType.WORKFLOW_RUN_COMPLETED:
                # 工作流运行完成
                data = json.loads(event.data) if isinstance(event.data, str) else event.data
                yield {
                    "type": "completed",
                    "data": data
                }
            elif event.type == WorkflowEventType.WORKFLOW_RUN_ERROR:
                # 工作流运行错误
                error = json.loads(event.data) if isinstance(event.data, str) else event.data
                yield {
                    "type": "error",
                    "data": error
                }


def register_coze_workflow_service() -> Optional[CozeWorkflowService]:
    """
    注册Coze工作流服务
    
    从环境变量读取配置并注册服务
    
    Returns:
        注册的服务实例，如果配置缺失则返回None
    """
    api_token = os.environ.get("COZE_API_TOKEN")
    api_base = os.environ.get("COZE_API_BASE")
    default_workflow_id = os.environ.get("COZE_DEFAULT_WORKFLOW_ID")
    
    if not api_token:
        return None
    
    # 创建服务实例
    service = CozeWorkflowService(
        api_token=api_token,
        api_base=api_base,
        workflow_id=default_workflow_id
    )
    
    # 注册到全局服务注册表
    AIServiceRegistry.register(service)
    
    return service
