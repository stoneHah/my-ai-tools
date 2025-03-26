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


class ASRRequest(BaseModel):
    """语音识别请求模型"""
    service_name: Optional[str] = Field("dashscope", description="服务名称，如dashscope等")
    audio_url: Optional[str] = Field(None, description="音频文件URL")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="额外参数")

    class Config:
        schema_extra = {
            "example": {
                "service_name": "dashscope",
                "audio_url": "https://example.com/audio.mp3",
                "parameters": {}
            }
        }


class ASRResponse(BaseModel):
    """语音识别响应模型"""
    id: str = Field(..., description="响应ID")
    text: str = Field(..., description="识别出的文本内容")
    status: str = Field("success", description="识别状态")


class ServiceInfoResponse(BaseModel):
    """服务信息响应模型"""
    name: str = Field(..., description="服务名称")
    type: str = Field(..., description="服务类型")
    description: Optional[str] = Field(None, description="服务描述")


class VideoUrlRequest(BaseModel):
    """视频下载URL请求模型"""
    text_info: Optional[str] = Field(None, description="附加文本信息")


class VideoUrlResponse(BaseModel):
    """视频下载URL响应模型"""
    download_url: str = Field(..., description="视频下载URL")
    cover_url: Optional[str] = Field(None, description="视频封面URL")
    title: Optional[str] = Field(None, description="视频标题")
    duration: Optional[int] = Field(None, description="视频时长（秒）")
    size: Optional[int] = Field(None, description="视频大小（字节）")
    format: Optional[str] = Field(None, description="视频格式")
    quality: Optional[str] = Field(None, description="视频质量")
    extra_info: Dict[str, Any] = Field(default_factory=dict, description="额外信息")


class ServicesListResponse(BaseModel):
    """服务列表响应模型"""
    services: Dict[str, List[str]] = Field(..., description="按类型分组的服务列表")
