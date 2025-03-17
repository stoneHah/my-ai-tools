"""
API模型定义
定义API请求和响应的数据模型
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求模型"""
    service_name: Optional[str] = Field("coze", description="服务名称，如coze、openai等")
    service_type: Optional[str] = Field("chat", description="服务类型，如chat、workflow等")
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="会话ID，如果提供将在现有会话中添加消息")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="额外参数，如bot_id等")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str = Field(..., description="响应ID")
    conversation_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="AI回复内容")
    role: str = Field("assistant", description="回复角色，通常为assistant")


class ChatStreamResponse(BaseModel):
    """聊天流式响应模型"""
    id: str = Field(..., description="响应ID")
    conversation_id: str = Field(..., description="会话ID")
    delta: str = Field(..., description="本次增量内容")
    content: str = Field(..., description="当前累积的完整内容")
    role: str = Field("assistant", description="回复角色，通常为assistant")




class ConversationResponse(BaseModel):
    """会话响应模型"""
    conversation_id: str = Field(..., description="会话ID")
    created_at: Optional[str] = Field(None, description="创建时间")


class WorkflowRequest(BaseModel):
    """工作流请求模型"""
    message: str = Field(..., description="工作流输入")
    conversation_id: Optional[str] = Field(None, description="会话ID，如果提供将在现有会话中添加消息")
    stream: bool = Field(False, description="是否使用流式响应")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="额外参数，如workflow_id等")


class WorkflowResponse(BaseModel):
    """工作流响应模型"""
    id: str = Field(..., description="响应ID")
    conversation_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="工作流输出")
    role: str = Field("assistant", description="角色，通常为assistant")


class ServiceInfoResponse(BaseModel):
    """服务信息响应模型"""
    name: str = Field(..., description="服务名称")
    type: str = Field(..., description="服务类型")
    description: Optional[str] = Field(None, description="服务描述")


class ServicesListResponse(BaseModel):
    """服务列表响应模型"""
    services: Dict[str, List[str]] = Field(..., description="按类型分组的服务列表")
