"""
工作流API路由
提供工作流相关的API端点
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json

from api.models import ChatRequest
from ai_services.base import AIServiceRegistry

router = APIRouter(prefix="/ai", tags=["workflow"])

@router.post("/workflow")
async def run_workflow(request: ChatRequest) -> Dict[str, Any]:
    """
    运行工作流（非流式）
    
    Args:
        request: 工作流请求
        
    Returns:
        工作流运行结果
    """
    # 获取服务
    service = AIServiceRegistry.get_service(
        service_name=request.service_name,
        service_type=request.service_type
    )
    
    if not service:
        raise HTTPException(
            status_code=404,
            detail=f"服务未找到: {request.service_name} (类型: {request.service_type})"
        )
    
    # 运行工作流
    try:
        result = await service.chat_completion(
            messages=request.messages,
            **request.parameters
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"工作流运行失败: {str(e)}"
        )

@router.post("/workflow/stream")
async def stream_workflow(request: ChatRequest) -> StreamingResponse:
    """
    流式运行工作流
    
    Args:
        request: 工作流请求
        
    Returns:
        流式工作流运行结果
    """
    # 获取服务
    service = AIServiceRegistry.get_service(
        service_name=request.service_name,
        service_type=request.service_type
    )
    
    if not service:
        raise HTTPException(
            status_code=404,
            detail=f"服务未找到: {request.service_name} (类型: {request.service_type})"
        )
    
    # 流式运行工作流
    try:
        async def generate():
            try:
                async for chunk in service.stream_chat_completion(
                    messages=request.messages,
                    **request.parameters
                ):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_json = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {error_json}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"工作流流式运行失败: {str(e)}"
        )
