"""
语音克隆API模型定义
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CloneVoiceRequest(BaseModel):
    """创建克隆音色请求"""
    sample_url: str = Field(..., description="样本音频URL")
    voice_name: str = Field(..., description="音色名称")
    user_id: str = Field(..., description="用户ID")
    app_id: str = Field(..., description="应用ID")
    description: Optional[str] = Field(None, description="音色描述")


class CloneVoiceResponse(BaseModel):
    """创建克隆音色响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    user_id: str = Field(..., description="用户ID")
    app_id: str = Field(..., description="应用ID")
    sample_url: str = Field(..., description="样本URL")
    voice_name: str = Field(..., description="音色名称")


class CloneTaskQueryRequest(BaseModel):
    """查询克隆任务请求"""
    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    app_id: str = Field(..., description="应用ID")


class CloneTaskQueryResponse(BaseModel):
    """查询克隆任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    voice_id: Optional[str] = Field(None, description="生成的音色ID")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class CloneVoiceListRequest(BaseModel):
    """获取克隆音色列表请求"""
    user_id: str = Field(..., description="用户ID")
    app_id: str = Field(..., description="应用ID")
    platform: Optional[str] = Field(None, description="平台代码")


class CloneVoiceDetail(BaseModel):
    """克隆音色详情"""
    voice_id: str = Field(..., description="音色ID")
    name: str = Field(..., description="音色名称")
    description: Optional[str] = Field(None, description="音色描述")
    user_id: str = Field(..., description="用户ID")
    app_id: str = Field(..., description="应用ID")
    platform: str = Field(..., description="平台代码")
    original_sample_url: Optional[str] = Field(None, description="原始样本URL")
    languages: List[str] = Field(default=[], description="支持的语言代码列表")
    is_streaming: bool = Field(..., description="是否支持流式接口")
    created_at: str = Field(..., description="创建时间")


class CloneVoiceListResponse(BaseModel):
    """获取克隆音色列表响应"""
    total: int = Field(..., description="总数")
    voices: List[CloneVoiceDetail] = Field(..., description="音色列表")


class TTSCloneSynthesizeRequest(BaseModel):
    """使用克隆音色合成语音请求"""
    text: str = Field(..., description="要合成的文本")
    voice_id: str = Field(..., description="克隆音色ID")
    user_id: str = Field(..., description="用户ID")
    app_id: str = Field(..., description="应用ID")
    service_name: str = Field("cosyvoice", description="服务名称")


class TTSCloneSynthesizeOSSRequest(TTSCloneSynthesizeRequest):
    """使用克隆音色合成语音并保存到OSS请求"""
    object_key: Optional[str] = Field(None, description="OSS对象键名/路径")
    oss_provider: Optional[str] = Field("aliyun", description="OSS提供商")


class TTSCloneSynthesizeResponse(BaseModel):
    """使用克隆音色合成语音响应"""
    audio_url: str = Field(..., description="音频URL")
    voice_id: str = Field(..., description="音色ID")
    text: str = Field(..., description="合成的文本")
    format: str = Field(..., description="音频格式")
