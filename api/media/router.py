"""
媒体工具API路由模块
提供与媒体相关的工具API端点
"""
from fastapi import APIRouter, HTTPException
import json
import uuid
import os
import logging
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

import ffmpeg

from .models import VideoUrlRequest, VideoUrlResponse, ExtractAudioRequest, ExtractAudioResponse
from ai_services.base import AIServiceRegistry
from ai_services.storage.registry import get_storage_service

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
        response = await service.run_workflow(
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


@router.post("/extract-audio", response_model=ExtractAudioResponse)
async def extract_audio_from_video(request: ExtractAudioRequest):
    """
    从视频中提取音频
    
    Args:
        request: 视频音频提取请求
        
    Returns:
        ExtractAudioResponse: 提取的音频URL和相关信息
    """
    # 获取存储服务
    storage_service = get_storage_service()
    if not storage_service:
        raise HTTPException(status_code=404, detail="找不到存储服务")
    
    # 创建临时目录用于处理文件
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            
            # 设置临时文件路径
            audio_filename = f"audio_{timestamp}_{unique_id}.{request.format}"
            audio_path = Path(temp_dir) / audio_filename
            
            logger.info(f"开始从视频URL提取音频: {request.video_url}")
            
            # 使用ffmpeg-python从URL提取音频
            try:
                # 设置音频编码器 - 根据格式选择正确的编码器
                audio_codec = None
                if request.format == 'aac':
                    audio_codec = 'copy'
                elif request.format == 'mp3':
                    audio_codec = 'libmp3lame'
                elif request.format == 'opus':
                    audio_codec = 'libopus'
                elif request.format == 'vorbis':
                    audio_codec = 'libvorbis'
                else:
                    # 默认尝试使用与格式同名的编码器
                    audio_codec = f'lib{request.format}'
                
                # 构建ffmpeg处理流程
                logger.info(f"使用ffmpeg-python提取音频，格式: {request.format}, 编码器: {audio_codec}")
                try:
                    (
                        ffmpeg
                        .input(request.video_url)
                        .output(str(audio_path), acodec=audio_codec, vn=None)
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True)
                    )
                    
                    # 检查输出文件是否存在且大小不为0
                    if not audio_path.exists() or audio_path.stat().st_size == 0:
                        logger.warning(f"未能提取到音频: 输出文件不存在或为空")
                        return ExtractAudioResponse(
                            id=f"audio_{unique_id}",
                            audio_url="",
                            format=request.format,
                            code="NO_AUDIO_STREAM",
                            message="视频文件不包含任何音频流"
                        )
                    
                    logger.info(f"音频提取成功: {audio_path}")
                except ffmpeg.Error as e:
                    error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
                    logger.error(f"ffmpeg执行失败: {error_message}")
                    
                    # 检查是否是"Output file does not contain any stream"错误
                    if "Output file does not contain any stream" in error_message:
                        logger.warning("检测到视频没有音频流")
                        return ExtractAudioResponse(
                            id=f"audio_{unique_id}",
                            audio_url="",
                            format=request.format,
                            code="NO_AUDIO_STREAM",
                            message="视频文件不包含任何音频流"
                        )
                    else:
                        # 其他ffmpeg错误
                        raise HTTPException(status_code=500, detail=f"音频提取失败: {error_message}")
                
                # 上传到OSS
                object_key = f"audio/{audio_filename}"
                audio_url = await storage_service.upload_file(
                    file_path=str(audio_path),
                    object_key=object_key,
                    content_type=f"audio/{request.format}"
                )
                
                logger.info(f"音频提取完成并上传到OSS: {audio_url}")
                
                # 构建响应
                return ExtractAudioResponse(
                    id=f"audio_{unique_id}",
                    audio_url=audio_url,
                    object_key=object_key,
                    format=request.format,
                    code="SUCCESS",
                    message="音频提取成功"
                )
            except Exception as e:
                logger.error(f"从视频提取音频出错: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"从视频提取音频出错: {str(e)}")
            
        except Exception as e:
            logger.error(f"从视频提取音频出错: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"从视频提取音频出错: {str(e)}")
