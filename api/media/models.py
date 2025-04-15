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
    object_key: Optional[str] = Field(None, description="OSS对象键")


class AudioConvertRequest(BaseModel):
    """音频转码请求模型"""
    audio_url: str = Field(..., description="音频URL", alias="audioUrl")
    source_format: Optional[str] = Field(None, description="源音频格式，如果为None则自动检测", alias="sourceFormat")
    target_format: str = Field("mp3", description="目标音频格式，默认为mp3", alias="targetFormat")
    bitrate: Optional[str] = Field(None, description="目标音频比特率，如128k")
    sample_rate: Optional[int] = Field(None, description="目标音频采样率，如44100", alias="sampleRate")
    channels: Optional[int] = Field(None, description="目标音频声道数，如2表示立体声")
    object_key: Optional[str] = Field(None, description="自定义OSS对象键，如果不提供则自动生成", alias="objectKey")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True


class AudioConvertResponse(BaseModel):
    """音频转码响应模型"""
    id: str = Field(..., description="响应ID")
    audio_url: str = Field(..., description="转码后的音频URL")
    source_format: str = Field(..., description="源音频格式")
    target_format: str = Field(..., description="目标音频格式")
    object_key: str = Field(..., description="OSS对象键")
    duration: Optional[float] = Field(None, description="音频时长（秒）")

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True
