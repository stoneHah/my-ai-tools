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

from .models import (
    VideoUrlRequest, VideoUrlResponse, 
    ExtractAudioRequest, ExtractAudioResponse,
    AudioConvertRequest, AudioConvertResponse
)
from ai_services.base import AIServiceRegistry
from ai_services.storage.registry import get_storage_service
from common.exceptions import NotFoundError, MediaProcessingError
from common.utils import get_audio_duration_from_bytes, get_audio_duration

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
        raise NotFoundError(message=f"找不到服务: {service_name}")
    
    # 验证是否为工作流服务
    if service.service_type != "workflow":
        raise NotFoundError(message=f"服务 {service_name} 不是工作流服务")
    
    # 准备工作流输入参数
    input_params = {
        "input": request.text_info,
    }
    
    # 获取工作流ID 
    workflow_id = os.getenv("COZE_VIDEO_DOWNLOAD_WORKFLOW_ID")
    if not workflow_id:
        raise Exception(message="未提供工作流ID")
    
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
        raise MediaProcessingError(message=f"获取视频下载URL出错: {str(e)}")


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
        raise NotFoundError(message="找不到存储服务")
    
    # 创建临时目录用于处理文件
    with tempfile.TemporaryDirectory() as temp_dir:
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # 设置临时文件路径
        audio_filename = f"audio_{timestamp}_{unique_id}.{request.format}"
        audio_path = Path(temp_dir) / audio_filename
        
        logger.info(f"开始从视频URL提取音频: {request.video_url}")
        
        # 使用ffmpeg-python从URL提取音频
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
                raise MediaProcessingError(message="视频文件不包含任何音频流")
            else:
                # 其他ffmpeg错误
                raise MediaProcessingError(message=f"音频提取失败: {error_message}")
        
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


@router.post("/convert-audio", response_model=AudioConvertResponse)
async def convert_audio_format(request: AudioConvertRequest):
    """
    将音频从一种格式转换为另一种格式
    
    Args:
        request: 音频转码请求
        
    Returns:
        AudioConvertResponse: 转码后的音频URL和相关信息
    """
    # 获取存储服务
    storage_service = get_storage_service()
    if not storage_service:
        raise NotFoundError(message="找不到存储服务")
    
    # 创建临时目录用于处理文件
    with tempfile.TemporaryDirectory() as temp_dir:
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # 下载源音频文件
        source_audio_path = Path(temp_dir) / f"source_{timestamp}_{unique_id}"
        
        # 如果提供了源格式，则添加扩展名
        if request.source_format:
            source_audio_path = source_audio_path.with_suffix(f".{request.source_format}")
        
        # 设置输出文件路径
        target_audio_filename = f"converted_{timestamp}_{unique_id}.{request.target_format}"
        target_audio_path = Path(temp_dir) / target_audio_filename
        
        logger.info(f"开始处理音频转码请求: {request.audio_url} -> {request.target_format}")
        
        # 下载源音频文件
        try:
            # 方法1：使用aiohttp直接下载文件
            import aiohttp
            from common.utils import download_file_content
            
            logger.info(f"尝试使用aiohttp下载源音频文件: {request.audio_url}")
            try:
                audio_data = await download_file_content(request.audio_url)
                
                # 保存到临时文件
                with open(source_audio_path, "wb") as f:
                    f.write(audio_data)
                
                logger.info(f"使用aiohttp成功下载源音频文件: {len(audio_data)} 字节")
            except Exception as e:
                logger.warning(f"使用aiohttp下载失败，尝试使用ffmpeg下载: {str(e)}")
                
                # 方法2：使用ffmpeg下载
                try:
                    # 使用ffmpeg直接下载，不进行转码
                    logger.info(f"尝试使用ffmpeg下载源音频文件: {request.audio_url}")
                    ffmpeg_download_cmd = [
                        "ffmpeg", "-y", "-i", request.audio_url, 
                        "-c", "copy", str(source_audio_path)
                    ]
                    
                    # 执行命令并捕获输出
                    process = subprocess.run(
                        ffmpeg_download_cmd,
                        capture_output=True,
                        text=True,
                        check=False  # 不自动抛出异常，我们自己处理
                    )
                    
                    # 检查命令执行结果
                    if process.returncode != 0:
                        error_message = process.stderr
                        logger.error(f"ffmpeg下载失败: {error_message}")
                        raise Exception(f"ffmpeg下载失败: {error_message}")
                    
                    logger.info(f"使用ffmpeg成功下载源音频文件")
                except Exception as ffmpeg_error:
                    logger.error(f"使用ffmpeg下载失败: {str(ffmpeg_error)}")
                    raise Exception(f"下载源音频文件失败: {str(ffmpeg_error)}")
            
            # 检查源文件是否成功下载
            if not source_audio_path.exists() or source_audio_path.stat().st_size == 0:
                raise MediaProcessingError(message="下载源音频文件失败: 文件不存在或为空")
            
            logger.info(f"源音频文件下载成功: {source_audio_path} ({source_audio_path.stat().st_size} 字节)")
            
            # 检测源文件格式（如果未提供）
            source_format = request.source_format
            if not source_format:
                try:
                    # 使用ffprobe获取文件信息
                    probe = ffmpeg.probe(str(source_audio_path))
                    # 获取第一个音频流的编解码器名称
                    for stream in probe['streams']:
                        if stream['codec_type'] == 'audio':
                            source_format = stream['codec_name']
                            logger.info(f"检测到源音频编解码器: {source_format}")
                            break
                    
                    # 如果没有找到音频流，尝试获取格式名称
                    if not source_format and 'format' in probe:
                        source_format = probe['format']['format_name'].split(',')[0]
                        logger.info(f"使用容器格式作为源格式: {source_format}")
                    
                    if not source_format:
                        source_format = "unknown"
                        logger.warning("无法检测源音频格式，使用'unknown'")
                except Exception as e:
                    logger.warning(f"无法检测源音频格式: {str(e)}")
                    source_format = "unknown"
            
            logger.info(f"源音频格式: {source_format}, 目标格式: {request.target_format}")
            
            # 设置音频编码器和参数
            output_args = {}
            
            # 设置音频编码器
            if request.target_format == 'mp3':
                output_args['acodec'] = 'libmp3lame'
            elif request.target_format == 'aac':
                output_args['acodec'] = 'aac'
            elif request.target_format == 'wav':
                output_args['acodec'] = 'pcm_s16le'
            elif request.target_format == 'flac':
                output_args['acodec'] = 'flac'
            elif request.target_format == 'opus':
                output_args['acodec'] = 'libopus'
            elif request.target_format == 'ogg':
                output_args['acodec'] = 'libvorbis'
            else:
                # 默认尝试使用与格式同名的编码器
                output_args['acodec'] = f'lib{request.target_format}'
            
            # 设置比特率
            if request.bitrate:
                output_args['audio_bitrate'] = request.bitrate
            
            # 设置采样率
            if request.sample_rate:
                output_args['ar'] = request.sample_rate
            
            # 设置声道数
            if request.channels:
                output_args['ac'] = request.channels
            
            # 执行转码
            logger.info(f"开始音频转码: {source_audio_path} -> {target_audio_path}")
            logger.info(f"转码参数: {output_args}")
            
            try:
                (
                    ffmpeg
                    .input(str(source_audio_path))
                    .output(str(target_audio_path), **output_args)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                # 检查输出文件是否存在且大小不为0
                if not target_audio_path.exists() or target_audio_path.stat().st_size == 0:
                    raise MediaProcessingError(message="音频转码失败: 输出文件不存在或为空")
                
                logger.info(f"音频转码成功: {target_audio_path} ({target_audio_path.stat().st_size} 字节)")
                
                # 获取音频时长
                audio_duration = 0.0
                try:
                    audio_duration = get_audio_duration(str(target_audio_path))
                    logger.info(f"获取到音频时长: {audio_duration} 秒")
                except Exception as e:
                    logger.warning(f"获取音频时长失败: {str(e)}")
                
                # 生成对象键
                object_key = request.object_key or f"audio/converted/{target_audio_filename}"
                
                # 上传到OSS
                audio_url = await storage_service.upload_file(
                    file_path=str(target_audio_path),
                    object_key=object_key,
                    content_type=f"audio/{request.target_format}"
                )
                
                logger.info(f"转码后的音频已上传到OSS: {audio_url}")
                
                # 构建响应
                return AudioConvertResponse(
                    id=f"convert_{unique_id}",
                    audio_url=audio_url,
                    source_format=source_format,
                    target_format=request.target_format,
                    object_key=object_key,
                    duration=audio_duration
                )
                
            except ffmpeg.Error as e:
                error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
                logger.error(f"音频转码失败: {error_message}")
                raise MediaProcessingError(message=f"音频转码失败: {error_message}")
                
        except subprocess.CalledProcessError as e:
            error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logger.error(f"下载源音频文件失败: {error_message}")
            raise MediaProcessingError(message=f"下载源音频文件失败: {error_message}")
        except Exception as e:
            logger.error(f"音频转码过程中发生错误: {str(e)}", exc_info=True)
            raise MediaProcessingError(message=f"音频转码失败: {str(e)}")
