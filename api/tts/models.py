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
