"""
图像生成模块数据模型定义
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ImageGenerationRequest(BaseModel):
    """图像生成请求模型"""
    service_name: Optional[str] = Field("coze", description="服务名称，如coze等")
    prompt: str = Field(..., description="图像生成提示词")
    aspect_ratio: Optional[str] = Field("1:1", description="图像宽高比，如'1:1', '16:9'等")
    model: Optional[str] = Field(None, description="使用的模型名称")
    num_images: Optional[int] = Field(default_factory=lambda: 1, description="生成图像的数量，默认为1")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class CreateImageTaskResponse(BaseModel):
    """创建图像生成任务响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    created_at: int = Field(..., description="任务创建时间戳")
    prompt: str = Field(..., description="使用的提示词")
    aspect_ratio: Optional[str] = Field(None, description="使用的宽高比")
    model: Optional[str] = Field(None, description="使用的模型")


class ImageTaskResultRequest(BaseModel):
    """获取图像生成任务结果请求模型"""
    task_id: str = Field(..., description="任务ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class ImageTaskResultResponse(BaseModel):
    """获取图像生成任务结果响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态，如pending、running、completed、failed、error等")
    images: Optional[List[str]] = Field(None, description="生成的图像URL列表，仅在completed状态时有值")
    error: Optional[str] = Field(None, description="错误信息，仅在failed或error状态时有值")
    completed_at: Optional[int] = Field(None, description="任务完成时间戳，仅在completed状态时有值")


class ImageServicesListResponse(BaseModel):
    """图像服务列表响应模型"""
    services: Dict[str, str] = Field(..., description="可用的图像生成服务列表")
