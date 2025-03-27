"""
ASR模块数据模型定义
"""
from typing import Dict, Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field


class ASRRequest(BaseModel):
    """语音识别请求模型"""
    service_name: Optional[str] = Field(None, description="服务名称")
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


T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """通用API响应模型"""
    code: int = Field(200, description="状态码，200表示成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field("", description="响应消息")
