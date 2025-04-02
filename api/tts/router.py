"""
TTS服务路由模块
提供TTS相关的API端点
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid
import os
import logging

from db.config import get_db
from ai_services.tts.base import TTSServiceBase
from ai_services.tts.models import TTSVoice, TTSPlatform, TTSVoiceCategory, TTSLanguage
from ai_services.tts.registry import get_tts_service, list_tts_services
from .models import (
    VoiceResponse, VoicePlatformResponse,
    VoiceCategoryResponse, VoiceLanguageResponse,
    SimpleVoicesListResponse,
    TTSSynthesizeRequest, TTSSynthesizeResponse, TTSSynthesizeOSSRequest
)

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/tts", tags=["tts"])


@router.get("/voices", response_model=SimpleVoicesListResponse, summary="获取TTS音色列表")
async def list_voices(
    platform: Optional[str] = Query(
        None, 
        description="平台代码，如volcengine",
        example="volcengine"
    ),
    category: Optional[str] = Query(
        None, 
        description="分类名称，如通用音色、视频配音、有声阅读",
        example="通用音色"
    ),
    language: Optional[str] = Query(
        None, 
        description="语言代码，如zh、en-US",
        example="zh"
    ),
    gender: Optional[str] = Query(
        None, 
        description="性别，如male、female",
        example="female",
        enum=["male", "female"]
    ),
    is_streaming: Optional[bool] = Query(
        None, 
        description="是否支持流式接口",
        example=True
    ),
    db: Session = Depends(get_db)
):
    """
    查询TTS音色列表，支持多种过滤条件
    
    Args:
        platform: 平台代码，如volcengine
        category: 分类名称，如通用音色、视频配音、有声阅读
        language: 语言代码，如zh、en-US
        gender: 性别，如male、female
        is_streaming: 是否支持流式接口
        
    Returns:
        SimpleVoicesListResponse: 简化的音色列表响应
    """
    # 构建查询
    query = db.query(TTSVoice).filter(TTSVoice.is_active == True)
    
    # 应用过滤条件
    if platform:
        query = query.join(TTSPlatform).filter(TTSPlatform.code == platform)
    
    if category:
        query = query.join(TTSVoiceCategory).filter(TTSVoiceCategory.name == category)
    
    if language:
        query = query.join(TTSVoice.languages).filter(TTSLanguage.code == language)
    
    if gender:
        query = query.filter(TTSVoice.gender == gender)
    
    if is_streaming is not None:
        query = query.filter(TTSVoice.is_streaming == is_streaming)
    
    # 执行查询
    voices = query.all()
    total = len(voices)
    
    # 构建简化的响应
    simple_voices = [
        {
            "voice_id": voice.voice_id,
            "name": voice.name,
            "gender": voice.gender,
            "description": voice.description
        }
        for voice in voices
    ]
    
    return {
        "total": total,
        "voices": simple_voices
    }


@router.get("/voices/{voice_id}", response_model=VoiceResponse, summary="获取指定ID的TTS音色详情")
async def get_voice(voice_id: str, db: Session = Depends(get_db)):
    """
    获取指定ID的TTS音色详情
    
    Args:
        voice_id: 音色ID
        
    Returns:
        VoiceResponse: 音色详情响应
    """
    voice = db.query(TTSVoice).filter(TTSVoice.voice_id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail=f"找不到音色: {voice_id}")
    
    return voice


@router.get("/platforms", response_model=List[VoicePlatformResponse], summary="获取所有TTS平台列表")
async def list_platforms(db: Session = Depends(get_db)):
    """
    获取所有TTS平台列表
    
    Returns:
        List[VoicePlatformResponse]: 平台列表
    """
    platforms = db.query(TTSPlatform).filter(TTSPlatform.is_active == True).all()
    return platforms


@router.get("/categories", response_model=List[VoiceCategoryResponse], summary="获取所有TTS音色分类")
async def list_categories(db: Session = Depends(get_db)):
    """
    获取所有TTS音色分类
    
    Returns:
        List[VoiceCategoryResponse]: 分类列表
    """
    categories = db.query(TTSVoiceCategory).all()
    return categories


@router.get("/languages", response_model=List[VoiceLanguageResponse], summary="获取所有支持的语言")
async def list_languages(db: Session = Depends(get_db)):
    """
    获取所有支持的语言
    
    Returns:
        List[VoiceLanguageResponse]: 语言列表
    """
    languages = db.query(TTSLanguage).all()
    return languages


@router.get("/services", summary="获取所有可用的TTS服务")
async def list_tts_services_endpoint():
    """
    获取所有可用的TTS服务
    
    Returns:
        Dict[str, str]: 服务名称到服务类型的映射
    """
    services = list_tts_services()
    return {"services": services}


@router.post("/synthesize", response_model=TTSSynthesizeResponse, summary="将文本合成为语音并保存到OSS")
async def synthesize_text_to_oss(request: TTSSynthesizeOSSRequest):
    """
    将文本合成为语音并保存到OSS
    
    Args:
        request: TTS合成请求
        
    Returns:
        TTSSynthesizeResponse: TTS合成响应
    """
    # 获取TTS服务
    service: TTSServiceBase = get_tts_service(request.service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到TTS服务: {request.service_name}")
    
    try:
        # 生成对象键
        object_key = request.object_key or f"tts/{uuid.uuid4()}.{request.format or 'mp3'}"
        
        # 合成语音并保存到OSS
        audio_url = await service.save_to_oss(
            text=request.text,
            voice_id=request.voice_id,
            object_key=object_key,
            # oss_provider=request.oss_provider,
            speed=request.speed,
            volume=request.volume,
            pitch=request.pitch,
            encoding=request.encoding
        )
        
        # 构建响应
        return {
            "request_id": str(uuid.uuid4()),
            "audio_url": audio_url,
            "object_key": object_key,
            "content_type": f"audio/{request.encoding}",
            "service_name": request.service_name
        }
    except Exception as e:
        logger.error(f"TTS合成并保存到OSS失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS合成并保存到OSS失败: {str(e)}")


@router.post("/synthesize/stream", summary="将文本合成为语音（流式）")
async def stream_synthesize_text(request: TTSSynthesizeRequest):
    """
    将文本合成为语音（流式）
    
    Args:
        request: TTS合成请求
        
    Returns:
        StreamingResponse: 流式音频响应
    """
    # 获取TTS服务
    service = get_tts_service(request.service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到TTS服务: {request.service_name}")
    
    try:
        # 创建流式生成器
        async def audio_generator():
            async for chunk in service.stream_synthesize(
                text=request.text,
                voice_id=request.voice_id,
                speed=request.speed,
                volume=request.volume,
                pitch=request.pitch,
                encoding=request.encoding
            ):
                yield chunk
        
        # 返回流式响应
        content_type = f"audio/{request.encoding or 'mp3'}"
        return StreamingResponse(
            audio_generator(),
            media_type=content_type,
            headers={
                "X-Request-ID": str(uuid.uuid4()),
                "X-Service-Name": request.service_name
            }
        )
    except Exception as e:
        logger.error(f"流式TTS合成失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"流式TTS合成失败: {str(e)}")


