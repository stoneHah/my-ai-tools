"""
API模型定义
定义API请求和响应的数据模型
"""
from typing import Dict, List, Optional, Any, Union, Generic, TypeVar
from pydantic import BaseModel, Field


class AIServiceInfo(BaseModel):
    """AI服务信息"""
    service_name: str = Field(..., description="服务名称")
    service_type: str = Field(..., description="服务类型")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    service_name: Optional[str] = Field("coze", description="服务名称，如coze、openai等")
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


class StreamChatResponse(BaseModel):
    """流式聊天响应模型"""
    id: str = Field(..., description="响应ID")
    message: str = Field(..., description="当前累积的消息")
    delta: str = Field(..., description="本次增量内容")
    conversation_id: str = Field(..., description="会话ID")
    is_final: bool = Field(False, description="是否为最终结果")


class ASRRequest(BaseModel):
    """语音识别请求模型"""
    service_name: str = Field(..., description="服务名称")
    audio_url: str = Field(..., description="音频文件URL")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class ASRResponse(BaseModel):
    """语音识别响应模型"""
    id: str = Field(..., description="响应ID")
    text: str = Field(..., description="识别出的文本")
    status: str = Field("success", description="状态")


class StreamASRResponse(BaseModel):
    """流式语音识别响应模型"""
    id: str = Field(..., description="响应ID")
    text: str = Field(..., description="当前累积的文本")
    delta: str = Field(..., description="本次增量内容")
    status: str = Field("success", description="状态")
    is_final: bool = Field(False, description="是否为最终结果")


class VideoUrlRequest(BaseModel):
    """视频URL请求模型"""
    text_info: str = Field(..., description="视频地址信息")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class VideoUrlResponse(BaseModel):
    """视频URL响应模型"""
    id: str = Field(..., description="响应ID")
    download_url: str = Field(..., description="处理后的视频URL")
    cover_url: str = Field(..., description="处理后的视频封面URL")


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


class ServicesListResponse(BaseModel):
    """服务列表响应模型"""
    services: Dict[str, List[str]] = Field(..., description="按类型分组的服务列表")


T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """通用API响应模型"""
    code: int = Field(200, description="状态码，200表示成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field("", description="响应消息")
