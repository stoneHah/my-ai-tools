"""
语音识别服务路由模块
提供语音识别相关的API端点
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import logging
import os
import uuid
import tempfile
from typing import Optional, Dict, Any

# 配置日志记录器
logger = logging.getLogger(__name__)

from api.models import (
    ASRRequest, ASRResponse
)
from ai_services.base import AIServiceRegistry

# 创建API路由器
router = APIRouter(prefix="/asr", tags=["asr"])


@router.post("/recognize", response_model=ASRResponse)
async def recognize_speech(request: ASRRequest):
    """
    通过URL进行语音识别
    
    Args:
        request: 包含音频URL的请求
        
    Returns:
        ASRResponse: 识别结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(request.service_name, "asr")
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音识别服务: {request.service_name}")
    
    # 检查是否提供了音频URL
    if not request.audio_url:
        raise HTTPException(status_code=400, detail="必须提供audio_url参数")
    
    # 调用服务
    try:
        response = await service.recognize(
            audio_url=request.audio_url,
            **request.parameters
        )
        
        # 构建响应
        return {
            "id": response.get("id", ""),
            "text": response.get("text", ""),
            "status": response.get("status", "success")
        }
    except Exception as e:
        logger.error(f"语音识别失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")


@router.post("/file", response_model=ASRResponse)
async def recognize_file(
    file: UploadFile = File(...),
    service_name: str = Form("dashscope"),
    parameters: str = Form("{}")
):
    """
    通过上传文件进行语音识别
    
    Args:
        file: 上传的音频文件
        service_name: 服务名称
        parameters: JSON格式的额外参数
        
    Returns:
        ASRResponse: 识别结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(service_name, "asr")
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音识别服务: {service_name}")
    
    # 解析参数
    try:
        params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="参数格式错误，必须是有效的JSON")
    
    # 保存上传的文件到临时目录
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 调用服务进行识别
        response = await service.recognize(
            audio_file_path=file_path,
            **params
        )
        
        # 构建响应
        return {
            "id": response.get("id", ""),
            "text": response.get("text", ""),
            "status": response.get("status", "success")
        }
    except Exception as e:
        logger.error(f"文件识别失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件识别失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")


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
            async for chunk in service.stream_recognize(
                audio_url=request.audio_url,
                **request.parameters
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


@router.post("/file/stream")
async def stream_recognize_file(
    file: UploadFile = File(...),
    service_name: str = Form("dashscope"),
    parameters: str = Form("{}")
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
    # 获取服务实例
    service = AIServiceRegistry.get_service(service_name, "asr")
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到语音识别服务: {service_name}")
    
    # 解析参数
    try:
        params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="参数格式错误，必须是有效的JSON")
    
    # 保存上传的文件到临时目录
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    # 保存文件
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 生成事件流
    async def event_generator():
        try:
            async for chunk in service.stream_recognize(
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
                    logger.warning(f"清理临时文件失败: {str(e)}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
