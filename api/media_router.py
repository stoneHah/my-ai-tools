"""
媒体工具API路由模块
提供与媒体相关的工具API端点
"""
from fastapi import APIRouter, HTTPException
import json
import uuid
import os
import logging
from datetime import datetime
from typing import Dict, Any

from api.models import VideoUrlRequest, VideoUrlResponse
from ai_services.base import AIServiceRegistry

# 设置日志记录器
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/tools/media", tags=["media"])


@router.post("/video-url", response_model=VideoUrlResponse)
async def get_video_download_url(request: VideoUrlRequest):
    """
    获取视频下载URL和封面
    
    Returns:
        VideoUrlResponse: 视频下载URL和封面信息
    """
    # 获取服务实例 - 使用coze服务
    service_name = "coze"  # 默认使用coze服务
    service_type = "workflow"  # 服务类型为workflow
    service = AIServiceRegistry.get_service(service_name, service_type)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到服务: {service_name}")
    
    # 验证是否为工作流服务
    if service.service_type != "workflow":
        raise HTTPException(status_code=400, detail=f"服务 {service_name} 不是工作流服务")
    
    # 准备工作流输入参数
    input_params = {
        "input": request.text_info,
    }
    
    # 获取工作流ID 
    workflow_id = os.getenv("COZE_VIDEO_DOWNLOAD_WORKFLOW_ID")
    if not workflow_id:
        raise HTTPException(status_code=400, detail="未提供工作流ID")
    
    # 调用服务
    try:
        # 直接调用run_workflow方法获取结果
        response: Dict[str, Any] = await service.run_workflow(
            workflow_id=workflow_id,
            input_params=input_params
        )

        logger.info(f"获取视频下载URL结果: {response}")
        
        # 构建响应
        return VideoUrlResponse(
            id=f"vid_{uuid.uuid4()}",
            download_url=response["video_url"],
            cover_url=response["cover"]
        )
    except Exception as e:
        logger.error(f"获取视频下载URL出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取视频下载URL出错: {str(e)}")
