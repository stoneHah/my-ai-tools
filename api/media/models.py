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
