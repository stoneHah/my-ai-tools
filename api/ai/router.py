"""
AI服务路由模块
提供统一的API端点访问各种AI服务
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import logging
import os

# 配置日志记录器
logger = logging.getLogger(__name__)

from .models import (
    ChatRequest, ChatResponse, ServicesListResponse,
    ConversationResponse
)
from ai_services.base import AIServiceRegistry

# 创建API路由器
router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/services", response_model=ServicesListResponse)
async def list_services():
    """
    列出所有可用的AI服务
    """
    services = AIServiceRegistry.list_services()
    return {"services": services}


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation():
    """
    为指定AI服务创建新会话
    
    Returns:
        ConversationResponse: 包含新会话ID的响应
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service("coze", "chat")
    if not service:
        raise HTTPException(status_code=404, detail="找不到服务: coze")
    
    # 调用服务
    try:
        conversation_id = await service.create_conversation()
        return {
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat()
        }
    except NotImplementedError:
        logger.warning("服务 coze 不支持创建会话")
        raise HTTPException(status_code=501, detail="服务 coze 不支持创建会话")
    except Exception as e:
        # 记录详细的异常信息
        logger.error(f"创建会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    与指定AI服务进行对话（非流式响应）
    
    Args:
        request: 聊天请求
        
    Returns:
        ChatResponse: 对话完成结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(request.service_name, request.service_type)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到服务: {request.service_name}")
    
    # 调用服务
    try:
        response = await service.chat_completion(
            message=request.message,
            conversation_id=request.conversation_id,
            **(request.parameters or {})
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务调用出错: {str(e)}")


async def _create_stream_response(service, request, bot_id=None):
    """
    创建流式响应的通用辅助函数
    
    Args:
        service: AI服务实例
        request: 聊天请求
        bot_id: 可选的指定Bot ID，如果提供则覆盖请求中的bot_id参数
        
    Returns:
        StreamingResponse: 流式响应对象
    """
    # 如果提供了特定的bot_id，则添加到参数中
    parameters = request.parameters or {}
    if bot_id:
        parameters["bot_id"] = bot_id
    
    # 生成事件流
    async def event_generator():
        try:
            async for chunk in service.stream_chat_completion(
                message=request.message,
                conversation_id=request.conversation_id,
                **parameters
            ):
                # 在API层将标准字典格式转换为SSE格式
                yield f"data: {json.dumps(chunk)}\n\n"
            
        except Exception as e:
            logger.error(f"流式对话失败: {str(e)}", exc_info=True)
            # 出错时发送错误信息
            error_json = {"error": {"message": str(e)}}
            yield f"data: {json.dumps(error_json)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.post("/chat/stream")
async def stream_chat_completion(request: ChatRequest):
    """
    与指定AI服务进行对话（流式响应）
    
    Args:
        request: 聊天请求
        
    Returns:
        StreamingResponse: 流式对话完成结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(request.service_name, request.service_type)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到服务: {request.service_name}")
    
    return await _create_stream_response(service, request)


@router.post("/image/prompt_refinement")
async def image_prompt_refinement(request: ChatRequest):
    """
    润色AI绘图提示词
    
    Args:
        request: 聊天请求
        
    Returns:
        StreamingResponse: 流式对话完成结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(request.service_name, request.service_type)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到服务: {request.service_name}")
    
    # 获取AI绘图提示词润色的Bot ID
    prompt_refinement_bot_id = os.getenv("COZE_DEFAULT_PROMPT_REFINEMENT_BOT_ID")
    if not prompt_refinement_bot_id:
        raise Exception("未找到AI绘图提示词润色的Bot ID")

    return await _create_stream_response(service, request, bot_id=prompt_refinement_bot_id)