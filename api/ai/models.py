"""
AI模块数据模型定义
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AIServiceInfo(BaseModel):
    """AI服务信息"""
    service_name: str = Field(..., description="服务名称")
    service_type: str = Field(..., description="服务类型")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    service_name: Optional[str] = Field("coze", description="服务名称，如coze、openai等")
    service_type: Optional[str] = Field("chat", description="服务类型，如chat、workflow等")
    message: str = Field(..., description="用户消息")
    conversation_id: Optional[str] = Field(None, description="会话ID，如果不提供则创建新会话")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: str = Field(..., description="响应ID")
    message: str = Field(..., description="AI回复消息")
    conversation_id: str = Field(..., description="会话ID")


class ConversationRequest(BaseModel):
    """创建会话请求模型"""
    service_name: Optional[str] = Field("coze", description="服务名称，如coze、openai等")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class ConversationResponse(BaseModel):
    """创建会话响应模型"""
    conversation_id: str = Field(..., description="会话ID")
    created_at: Optional[str] = Field(None, description="创建时间")


class StreamChatResponse(BaseModel):
    """流式聊天响应模型"""
    id: str = Field(..., description="响应ID")
    message: str = Field(..., description="当前累积的消息")
    delta: str = Field(..., description="本次增量内容")
    conversation_id: str = Field(..., description="会话ID")
    is_final: bool = Field(False, description="是否为最终结果")


class WorkflowRequest(BaseModel):
    """工作流请求模型"""
    service_name: Optional[str] = Field("coze", description="服务名称，如coze等")
    workflow_id: str = Field(..., description="工作流ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="工作流输入参数")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class WorkflowResponse(BaseModel):
    """工作流响应模型"""
    id: str = Field(..., description="响应ID")
    result: Dict[str, Any] = Field(..., description="工作流执行结果")


class StreamWorkflowResponse(BaseModel):
    """流式工作流响应模型"""
    id: str = Field(..., description="响应ID")
    result: Dict[str, Any] = Field(..., description="当前累积的结果")
    delta: Dict[str, Any] = Field(..., description="本次增量内容")
    is_final: bool = Field(False, description="是否为最终结果")


class BroadcastScriptsRequest(BaseModel):
    """批量生成口播文案请求模型"""
    topic: str = Field(..., description="口播文案主题")
    count: int = Field(5, description="生成文案数量，默认5个", ge=1, le=20)
    service_name: Optional[str] = Field("coze", description="服务名称")
    service_type: Optional[str] = Field("workflow", description="服务类型")


class BroadcastScriptsResponse(BaseModel):
    """批量生成口播文案响应模型"""
    scripts: List[str] = Field(..., description="生成的口播文案列表")


class RewriteExplosiveContentRequest(BaseModel):
    """爆款文案改写请求模型"""
    url: str = Field(..., description="需要改写的内容链接")
    service_name: Optional[str] = Field("coze", description="服务名称")
    service_type: Optional[str] = Field("workflow", description="服务类型")


class RewriteExplosiveContentResponse(BaseModel):
    """爆款文案改写响应模型"""
    content: str = Field(..., description="改写后的爆款文案")


class ServicesListResponse(BaseModel):
    """服务列表响应模型"""
    services: Dict[str, List[str]] = Field(..., description="按类型分组的服务列表")
