"""
TTS模块数据模型定义
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class VoiceLanguageResponse(BaseModel):
    """语言响应模型"""
    id: int
    name: str
    code: str
    
    class Config:
        orm_mode = True


class VoiceCategoryResponse(BaseModel):
    """音色分类响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        orm_mode = True


class VoicePlatformResponse(BaseModel):
    """平台响应模型"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    
    class Config:
        orm_mode = True


class VoiceResponse(BaseModel):
    """音色响应模型"""
    id: int
    voice_id: str
    name: str
    gender: Optional[str] = None
    description: Optional[str] = None
    is_streaming: bool
    is_active: bool
    platform: VoicePlatformResponse
    category: Optional[VoiceCategoryResponse] = None
    languages: List[VoiceLanguageResponse] = []
    
    class Config:
        orm_mode = True


class VoicesListResponse(BaseModel):
    """音色列表响应模型"""
    total: int
    voices: List[VoiceResponse]


class SimpleVoiceResponse(BaseModel):
    """简化的音色响应模型"""
    voice_id: str
    name: str
    gender: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        orm_mode = True


class SimpleVoicesListResponse(BaseModel):
    """简化的音色列表响应模型"""
    total: int
    voices: List[SimpleVoiceResponse]


class TTSSynthesizeRequest(BaseModel):
    """TTS合成请求模型"""
    text: str = Field(..., description="要合成的文本")
    voice_id: str = Field(..., description="音色ID")
    service_name: str = Field("volcengine", description="TTS服务名称")
    speed: Optional[float] = Field(1.0, description="语速，范围0.5-2.0")
    volume: Optional[float] = Field(1.0, description="音量，范围0.5-2.0")
    pitch: Optional[float] = Field(1.0, description="音调，范围0.5-2.0")
    format: Optional[str] = Field("mp3", description="音频格式，如mp3、wav")
    encoding: str = Field("mp3", description="音频格式，如mp3、wav、ogg等")


class TTSSynthesizeOSSRequest(TTSSynthesizeRequest):
    """TTS合成并保存到OSS的请求"""
    object_key: Optional[str] = Field(None, description="OSS对象键名/路径，如果不提供则自动生成")
    oss_provider: str = Field("aliyun", description="OSS提供商，默认为阿里云")


class TTSSynthesizeResponse(BaseModel):
    """TTS合成响应模型"""
    request_id: str = Field(..., description="请求ID")
    audio_url: Optional[str] = Field(None, description="音频URL，非流式响应时提供")
    content_type: str = Field(..., description="内容类型，如audio/mp3")
    service_name: str = Field(..., description="使用的TTS服务名称")
