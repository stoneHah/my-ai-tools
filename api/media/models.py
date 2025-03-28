"""
媒体模块数据模型定义
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class VideoUrlRequest(BaseModel):
    """视频URL请求模型"""
    text_info: str = Field(..., description="视频地址信息")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class VideoUrlResponse(BaseModel):
    """视频URL响应模型"""
    id: str = Field(..., description="响应ID")
    download_url: str = Field(..., description="处理后的视频URL")
    cover_url: str = Field(..., description="处理后的视频封面URL")


class ExtractAudioRequest(BaseModel):
    """视频音频提取请求模型"""
    video_url: str = Field(..., description="视频URL")
    format: str = Field("mp3", description="音频格式，默认为mp3")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class ExtractAudioResponse(BaseModel):
    """视频音频提取响应模型"""
    id: str = Field(..., description="响应ID")
    audio_url: str = Field(..., description="提取的音频URL")
    format: str = Field(..., description="音频格式")
