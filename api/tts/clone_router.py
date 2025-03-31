"""
语音克隆服务路由模块
提供语音克隆相关的API端点
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Response, Path
from sqlalchemy.orm import Session
import uuid
import datetime
import logging

from db.config import get_db
from ai_services.tts.base import TTSServiceBase
from ai_services.tts.clone_base import VoiceCloneServiceBase
from ai_services.tts.models import TTSPlatform, TTSLanguage
from ai_services.tts.clone_models import TTSCloneVoice, TTSCloneVoiceLanguage, TTSCloneTask
from ai_services.tts.registry import get_tts_service
from ai_services.tts.clone_registry import get_voice_clone_service, list_voice_clone_services
from .clone_models import (
    CloneVoiceRequest, CloneVoiceResponse,
    CloneTaskQueryRequest, CloneTaskQueryResponse,
    CloneVoiceListRequest, CloneVoiceListResponse, CloneVoiceDetail,
    TTSCloneSynthesizeRequest, TTSCloneSynthesizeOSSRequest, TTSCloneSynthesizeResponse
)

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/tts/clone", tags=["tts-clone"])


@router.get("/services", summary="获取所有可用的语音克隆服务")
async def list_voice_clone_services_endpoint():
    """
    获取所有可用的语音克隆服务
    
    Returns:
        Dict[str, str]: 服务名称到服务类型的映射
    """
    services = list_voice_clone_services()
    return {"services": services}


@router.post("/voices", response_model=CloneVoiceResponse, summary="创建克隆音色")
async def create_clone_voice(request: CloneVoiceRequest, db: Session = Depends(get_db)):
    """
    创建克隆音色
    
    Args:
        request: 创建克隆音色请求
        
    Returns:
        CloneVoiceResponse: 创建克隆音色响应
    """
    # 获取语音克隆服务
    service_name = request.service_name if hasattr(request, 'service_name') else "cosyvoice"
    service: VoiceCloneServiceBase = get_voice_clone_service(service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音克隆服务: {service_name}")
    
    try:
        # 调用服务创建克隆音色
        result = await service.create_clone_voice(
            sample_url=request.sample_url,
            voice_name=request.voice_name,
            user_id=request.user_id,
            app_id=request.app_id
        )
        
        # 获取平台ID
        platform = db.query(TTSPlatform).filter(TTSPlatform.code == service_name).first()
        if not platform:
            raise HTTPException(status_code=404, detail=f"找不到平台: {service_name}")
        
        # 创建克隆任务记录
        clone_task = TTSCloneTask(
            task_id=result["task_id"],
            user_id=request.user_id,
            app_id=request.app_id,
            sample_url=request.sample_url,
            voice_name=request.voice_name,
            status=result["status"],
            platform_id=platform.id
        )
        
        db.add(clone_task)
        db.commit()
        
        return result
    except Exception as e:
        logger.error(f"创建克隆音色失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建克隆音色失败: {str(e)}")


@router.post("/tasks/{task_id}", response_model=CloneTaskQueryResponse, summary="查询克隆任务状态")
async def query_clone_task(
    task_id: str = Path(..., description="任务ID"),
    request: CloneTaskQueryRequest = None,
    db: Session = Depends(get_db)
):
    """
    查询克隆任务状态
    
    Args:
        task_id: 任务ID
        request: 查询克隆任务请求
        
    Returns:
        CloneTaskQueryResponse: 查询克隆任务响应
    """
    # 验证用户和应用权限
    if request:
        task = db.query(TTSCloneTask).filter(
            TTSCloneTask.task_id == task_id,
            TTSCloneTask.user_id == request.user_id,
            TTSCloneTask.app_id == request.app_id
        ).first()
    else:
        task = db.query(TTSCloneTask).filter(TTSCloneTask.task_id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"找不到克隆任务: {task_id}")
    
    # 获取平台代码
    platform_code = task.platform.code
    
    # 获取语音克隆服务
    service: VoiceCloneServiceBase = get_voice_clone_service(platform_code)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音克隆服务: {platform_code}")
    
    try:
        # 调用服务查询克隆任务状态
        result = await service.query_clone_task(task_id)
        
        # 更新任务状态
        task.status = result["status"]
        if result.get("voice_id"):
            task.result_voice_id = result["voice_id"]
            
            # 如果任务完成，创建克隆音色记录
            if result["status"] == "success" and not db.query(TTSCloneVoice).filter(TTSCloneVoice.voice_id == result["voice_id"]).first():
                # 创建克隆音色记录
                clone_voice = TTSCloneVoice(
                    voice_id=result["voice_id"],
                    name=task.voice_name,
                    description=f"由{task.voice_name}克隆生成的音色",
                    user_id=task.user_id,
                    app_id=task.app_id,
                    platform_id=task.platform_id,
                    original_sample_url=task.sample_url,
                    is_streaming=True,
                    is_active=True
                )
                
                db.add(clone_voice)
                
                # 添加默认支持的语言（中文和英文）
                zh_lang = db.query(TTSLanguage).filter(TTSLanguage.code == "zh").first()
                en_lang = db.query(TTSLanguage).filter(TTSLanguage.code == "en").first()
                
                if zh_lang:
                    db.add(TTSCloneVoiceLanguage(
                        clone_voice_id=clone_voice.id,
                        language_id=zh_lang.id
                    ))
                
                if en_lang:
                    db.add(TTSCloneVoiceLanguage(
                        clone_voice_id=clone_voice.id,
                        language_id=en_lang.id
                    ))
        
        db.commit()
        
        return result
    except Exception as e:
        logger.error(f"查询克隆任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询克隆任务失败: {str(e)}")


@router.get("/voices", response_model=CloneVoiceListResponse, summary="获取克隆音色列表")
async def list_clone_voices(
    user_id: str = Query(..., description="用户ID"),
    app_id: str = Query(..., description="应用ID"),
    platform: Optional[str] = Query(None, description="平台代码"),
    db: Session = Depends(get_db)
):
    """
    获取克隆音色列表
    
    Args:
        user_id: 用户ID
        app_id: 应用ID
        platform: 平台代码，如cosyvoice
        
    Returns:
        CloneVoiceListResponse: 克隆音色列表响应
    """
    # 构建查询
    query = db.query(TTSCloneVoice).filter(
        TTSCloneVoice.user_id == user_id,
        TTSCloneVoice.app_id == app_id,
        TTSCloneVoice.is_active == True
    )
    
    # 应用平台过滤
    if platform:
        query = query.join(TTSPlatform).filter(TTSPlatform.code == platform)
    
    # 执行查询
    clone_voices = query.all()
    total = len(clone_voices)
    
    # 构建响应
    voice_details = []
    for voice in clone_voices:
        # 获取支持的语言
        languages = [lang.language.code for lang in voice.languages]
        
        # 构建详情
        voice_detail = CloneVoiceDetail(
            voice_id=voice.voice_id,
            name=voice.name,
            description=voice.description,
            user_id=voice.user_id,
            app_id=voice.app_id,
            platform=voice.platform.code,
            original_sample_url=voice.original_sample_url,
            languages=languages,
            is_streaming=voice.is_streaming,
            created_at=voice.created_at.isoformat()
        )
        
        voice_details.append(voice_detail)
    
    return {
        "total": total,
        "voices": voice_details
    }


@router.get("/voices/{voice_id}", response_model=CloneVoiceDetail, summary="获取克隆音色详情")
async def get_clone_voice(
    voice_id: str = Path(..., description="音色ID"),
    user_id: str = Query(..., description="用户ID"),
    app_id: str = Query(..., description="应用ID"),
    db: Session = Depends(get_db)
):
    """
    获取克隆音色详情
    
    Args:
        voice_id: 音色ID
        user_id: 用户ID
        app_id: 应用ID
        
    Returns:
        CloneVoiceDetail: 克隆音色详情
    """
    # 查询克隆音色
    voice = db.query(TTSCloneVoice).filter(
        TTSCloneVoice.voice_id == voice_id,
        TTSCloneVoice.user_id == user_id,
        TTSCloneVoice.app_id == app_id,
        TTSCloneVoice.is_active == True
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail=f"找不到克隆音色: {voice_id}")
    
    # 获取支持的语言
    languages = [lang.language.code for lang in voice.languages]
    
    # 构建详情
    voice_detail = CloneVoiceDetail(
        voice_id=voice.voice_id,
        name=voice.name,
        description=voice.description,
        user_id=voice.user_id,
        app_id=voice.app_id,
        platform=voice.platform.code,
        original_sample_url=voice.original_sample_url,
        languages=languages,
        is_streaming=voice.is_streaming,
        created_at=voice.created_at.isoformat()
    )
    
    return voice_detail


@router.delete("/voices/{voice_id}", summary="删除克隆音色")
async def delete_clone_voice(
    voice_id: str = Path(..., description="音色ID"),
    user_id: str = Query(..., description="用户ID"),
    app_id: str = Query(..., description="应用ID"),
    db: Session = Depends(get_db)
):
    """
    删除克隆音色
    
    Args:
        voice_id: 音色ID
        user_id: 用户ID
        app_id: 应用ID
        
    Returns:
        删除结果
    """
    # 查询克隆音色
    voice = db.query(TTSCloneVoice).filter(
        TTSCloneVoice.voice_id == voice_id,
        TTSCloneVoice.user_id == user_id,
        TTSCloneVoice.app_id == app_id,
        TTSCloneVoice.is_active == True
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail=f"找不到克隆音色: {voice_id}")
    
    # 获取语音克隆服务
    service: VoiceCloneServiceBase = get_voice_clone_service(voice.platform.code)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音克隆服务: {voice.platform.code}")
    
    try:
        # 调用服务删除克隆音色
        result = await service.delete_clone_voice(voice_id, user_id, app_id)
        
        # 在数据库中标记为已删除
        voice.is_active = False
        db.commit()
        
        return result
    except Exception as e:
        logger.error(f"删除克隆音色失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除克隆音色失败: {str(e)}")


@router.put("/voices/{voice_id}", summary="更新克隆音色信息")
async def update_clone_voice(
    voice_id: str = Path(..., description="音色ID"),
    user_id: str = Query(..., description="用户ID"),
    app_id: str = Query(..., description="应用ID"),
    name: Optional[str] = Query(None, description="新的音色名称"),
    description: Optional[str] = Query(None, description="新的音色描述"),
    db: Session = Depends(get_db)
):
    """
    更新克隆音色信息
    
    Args:
        voice_id: 音色ID
        user_id: 用户ID
        app_id: 应用ID
        name: 新的音色名称
        description: 新的音色描述
        
    Returns:
        更新结果
    """
    # 查询克隆音色
    voice = db.query(TTSCloneVoice).filter(
        TTSCloneVoice.voice_id == voice_id,
        TTSCloneVoice.user_id == user_id,
        TTSCloneVoice.app_id == app_id,
        TTSCloneVoice.is_active == True
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail=f"找不到克隆音色: {voice_id}")
    
    # 获取语音克隆服务
    service: VoiceCloneServiceBase = get_voice_clone_service(voice.platform.code)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音克隆服务: {voice.platform.code}")
    
    try:
        # 调用服务更新克隆音色信息
        kwargs = {}
        if name:
            kwargs["name"] = name
        if description:
            kwargs["description"] = description
            
        result = await service.update_clone_voice(voice_id, user_id, app_id, **kwargs)
        
        # 在数据库中更新信息
        if name:
            voice.name = name
        if description:
            voice.description = description
            
        db.commit()
        
        return result
    except Exception as e:
        logger.error(f"更新克隆音色信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新克隆音色信息失败: {str(e)}")


@router.post("/synthesize", response_model=TTSCloneSynthesizeResponse, summary="使用克隆音色合成语音")
async def synthesize_with_clone_voice(request: TTSCloneSynthesizeOSSRequest, db: Session = Depends(get_db)):
    """
    使用克隆音色合成语音并保存到OSS
    
    Args:
        request: 合成请求
        
    Returns:
        TTSCloneSynthesizeResponse: 合成响应
    """
    # 验证用户和应用权限
    voice = db.query(TTSCloneVoice).filter(
        TTSCloneVoice.voice_id == request.voice_id,
        TTSCloneVoice.user_id == request.user_id,
        TTSCloneVoice.app_id == request.app_id,
        TTSCloneVoice.is_active == True
    ).first()
    
    if not voice:
        raise HTTPException(status_code=404, detail=f"找不到克隆音色或无权访问: {request.voice_id}")
    
    # 获取TTS服务
    service: TTSServiceBase = get_tts_service(request.service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到TTS服务: {request.service_name}")
    
    try:
        # 生成对象键
        object_key = request.object_key or f"tts/clone/{request.user_id}/{uuid.uuid4()}.{request.format or 'mp3'}"
        
        # 合成语音并保存到OSS
        audio_url = await service.save_to_oss(
            text=request.text,
            voice_id=request.voice_id,
            object_key=object_key,
            oss_provider=request.oss_provider,
            format=request.format,
            speed=request.speed,
            volume=request.volume,
            pitch=request.pitch
        )
        
        return {
            "audio_url": audio_url,
            "voice_id": request.voice_id,
            "text": request.text,
            "format": request.format or "mp3"
        }
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")
