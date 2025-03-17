"""
AI服务通用路由模块
提供统一的API接口访问各种AI服务
"""
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.models import ChatRequest, ChatResponse, ServicesListResponse
from ai_services.base import AIServiceRegistry

# 创建API路由器
router = APIRouter(prefix="/ai", tags=["ai"])

@router.get("/services", response_model=ServicesListResponse)
async def list_services(service_type: Optional[str] = None):
    """
    列出所有可用的AI服务
    
    Args:
        service_type: 可选的服务类型过滤
    """
    services = AIServiceRegistry.list_services(service_type)
    return {"services": services}

@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    与AI服务进行对话（非流式响应）
    
    Args:
        request: 聊天请求
    """
    try:
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="此端点不支持流式响应，请将stream参数设置为false或使用/chat/stream端点"
            )
        
        service = AIServiceRegistry.get_service(
            service_type=request.service_type,
            service_name=request.service_name
        )
        
        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"未找到服务: {request.service_name} (类型: {request.service_type})"
            )
        
        parameters = request.parameters or {}
        response = await service.chat_completion(
            messages=request.messages,
            **parameters
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用AI服务出错：{str(e)}")

@router.post("/chat/stream")
async def stream_chat_completion(request: ChatRequest):
    """
    与AI服务进行对话（流式响应）
    
    返回一个Server-Sent Events (SSE)流，客户端可以实时接收AI服务的回复
    """
    try:
        service = AIServiceRegistry.get_service(
            service_type=request.service_type,
            service_name=request.service_name
        )
        
        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"未找到服务: {request.service_name} (类型: {request.service_type})"
            )
        
        async def event_generator():
            """生成SSE事件流"""
            try:
                parameters = request.parameters or {}
                async for chunk in service.stream_chat_completion(
                    messages=request.messages,
                    **parameters
                ):
                    # 将每个块序列化为JSON并按SSE格式输出
                    if isinstance(chunk, dict):
                        chunk_json = chunk
                    else:
                        chunk_json = {"error": "无效的响应格式"}
                    
                    yield f"data: {chunk_json}\n\n"
                
                # 流结束标记
                yield "data: [DONE]\n\n"
            except Exception as e:
                # 出错时发送错误信息
                error_json = {"error": {"message": str(e)}}
                yield f"data: {error_json}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建流式响应时出错：{str(e)}")
