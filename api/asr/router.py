"""
语音识别API路由
"""
import os
import tempfile
import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from .models import ASRRequest, ASRResponse, StreamASRResponse, APIResponse
from ai_services.base import AIServiceRegistry

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/asr", tags=["asr"])


@router.post("/recognize", response_model=APIResponse[ASRResponse])
async def recognize_speech(request: ASRRequest):
    """
    语音识别接口 - 通过URL
    
    Args:
        request: 语音识别请求
        
    Returns:
        识别结果
    """
    try:
        # 获取服务名称和参数
        service_name = request.service_name or os.getenv("DEFAULT_ASR_MODEL")
        audio_url = request.audio_url
        params = request.parameters or {}
        
        # 获取语音识别服务
        service = AIServiceRegistry.get_service(service_name, "asr")
        if not service:
            raise HTTPException(status_code=404, detail=f"未找到语音识别服务: {service_name}")
        
        # 调用服务进行识别
        response = await service.recognize_url(audio_url=audio_url, **params)
        
        # 构建响应
        asr_response = ASRResponse(
            id=response.get("id", ""),
            text=response.get("text", ""),
            status=response.get("status", "success")
        )
        
        # 返回统一格式的响应
        return APIResponse(
            code=200,
            data=asr_response,
            message="语音识别成功"
        )
    except Exception as e:
        logger.error(f"语音识别失败: {str(e)}", exc_info=True)
        return APIResponse(
            code=500,
            data=None,
            message=f"语音识别失败: {str(e)}"
        )


@router.post("/recognize/stream")
async def stream_recognize_speech(request: ASRRequest):
    """
    通过URL进行流式语音识别
    
    Args:
        request: 包含音频URL的请求
        
    Returns:
        StreamingResponse: 流式识别结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(request.service_name, "asr")
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音识别服务: {request.service_name}")
    
    # 检查是否提供了音频URL
    if not request.audio_url:
        raise HTTPException(status_code=400, detail="必须提供audio_url参数")
    
    # 生成事件流
    async def event_generator():
        try:
            async for chunk in service.stream_recognize_url(
                audio_url=request.audio_url,
                **(request.parameters or {})
            ):
                # 在API层将标准字典格式转换为SSE格式
                yield f"data: {json.dumps(chunk)}\n\n"
            
        except Exception as e:
            logger.error(f"流式语音识别失败: {str(e)}", exc_info=True)
            # 出错时发送错误信息
            error_json = {"error": {"message": str(e)}}
            yield f"data: {json.dumps(error_json)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("/file", response_model=APIResponse[ASRResponse])
async def recognize_file(
    file: UploadFile = File(..., description="要识别的音频文件"),
    sample_rate: int = Form(16000, description="音频采样率，默认为16000Hz"),
    format: str = Form("wav", description="音频格式，如wav、mp3、aac等"),
    parameters: Optional[str] = Form("{}", description="其他参数，JSON格式字符串")
):
    """
    语音识别接口 - 通过文件上传
    
    Args:
        file: 上传的音频文件
        sample_rate: 音频采样率，默认为16000Hz
        format: 音频格式，如wav、mp3、aac等
        parameters: 额外参数，JSON字符串
        
    Returns:
        识别结果
    """
    # 创建临时文件
    fd, file_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
    os.close(fd)
    
    try:
        # 解析参数
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError:
            params = {}

        # 默认服务名称
        service_name = os.getenv("DEFAULT_ASR_SERVICE")
        
        # 获取语音识别服务
        service = AIServiceRegistry.get_service(service_name, "asr")
        if not service:
            raise HTTPException(status_code=404, detail=f"未找到语音识别服务: {service_name}")
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        params["sample_rate"] = sample_rate
        params["format"] = format
        
        # 调用服务进行识别
        response = await service.recognize_file(
            audio_file_path=file_path,
            **params
        )
        
        # 构建响应
        asr_response = ASRResponse(
            id=response.get("id", ""),
            text=response.get("text", ""),
            status=response.get("status", "success")
        )
        
        # 返回统一格式的响应
        return APIResponse(
            code=200,
            data=asr_response,
            message="文件识别成功"
        )
    except Exception as e:
        logger.error(f"文件识别失败: {str(e)}", exc_info=True)
        return APIResponse(
            code=500,
            data=None,
            message=f"文件识别失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"清理临时文件失败: {str(e)}")


@router.post("/file/stream")
async def stream_recognize_file(
    file: UploadFile = File(...),
    service_name: str = Form(...),
    parameters: Optional[str] = Form("{}")
):
    """
    通过上传文件进行流式语音识别
    
    Args:
        file: 上传的音频文件
        service_name: 服务名称
        parameters: JSON格式的额外参数
        
    Returns:
        StreamingResponse: 流式识别结果
    """
    # 创建临时文件
    fd, file_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
    os.close(fd)
    
    try:
        # 解析参数
        try:
            params = json.loads(parameters) if parameters else {}
        except json.JSONDecodeError:
            params = {}
        
        # 获取语音识别服务
        service = AIServiceRegistry.get_service(service_name, "asr")
        if not service:
            raise HTTPException(status_code=404, detail=f"未找到语音识别服务: {service_name}")
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 生成事件流
        async def event_generator():
            try:
                async for chunk in service.stream_recognize_file(
                    audio_file_path=file_path,
                    **params
                ):
                    # 在API层将标准字典格式转换为SSE格式
                    yield f"data: {json.dumps(chunk)}\n\n"
                
            except Exception as e:
                logger.error(f"流式语音识别失败: {str(e)}", exc_info=True)
                # 出错时发送错误信息
                error_json = {"error": {"message": str(e)}}
                yield f"data: {json.dumps(error_json)}\n\n"
            finally:
                # 清理临时文件
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"清理临时文件失败: {str(e)}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"流式文件识别失败: {str(e)}", exc_info=True)
        # 确保清理临时文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as clean_error:
                logger.error(f"清理临时文件失败: {str(clean_error)}")
        raise HTTPException(status_code=500, detail=f"流式文件识别失败: {str(e)}")
