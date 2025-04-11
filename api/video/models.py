"""
视频生成模块数据模型定义
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ImageToVideoRequest(BaseModel):
    """图生视频请求模型"""
    service_name: Optional[str] = Field("volcengine", description="服务名称，如volcengine等")
    prompt: Optional[str] = Field(None, description="视频生成提示词")
    image_url: str = Field(..., description="输入图片URL")
    ratio: Optional[str] = Field("9:16", description="视频宽高比，如'9:16'等")
    duration: Optional[int] = Field(5, description="视频时长(秒)，默认5秒")
    model: Optional[str] = Field(None, description="使用的模型名称")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class CreateVideoTaskResponse(BaseModel):
    """创建视频生成任务响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    created_at: int = Field(..., description="任务创建时间戳")


class VideoTaskResultRequest(BaseModel):
    """获取视频生成任务结果请求模型"""
    task_id: str = Field(..., description="任务ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")

class VideoInfo(BaseModel):
    video_url: str = Field(..., description="视频URL")
    object_key: str = Field(..., description="视频对象存储路径")

class VideoTaskResultResponse(BaseModel):
    """获取视频生成任务结果响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态，如pending、running、completed、failed、error等")
    video_info: Optional[VideoInfo] = Field(None, description="生成的视频信息，仅在completed状态时有值")
    error: Optional[str] = Field(None, description="错误信息，仅在failed或error状态时有值")
    completed_at: Optional[int] = Field(None, description="任务完成时间戳，仅在completed状态时有值")



class VideoServicesListResponse(BaseModel):
    """视频服务列表响应模型"""
    services: Dict[str, str] = Field(..., description="可用的视频生成服务列表")
