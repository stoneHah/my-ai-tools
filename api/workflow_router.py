"""
工作流API路由模块
提供与工作流交互的API端点
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from api.models import WorkflowRequest, WorkflowResponse
from ai_services.base import AIServiceRegistry

# 创建API路由器
router = APIRouter(prefix="/ai/workflow", tags=["workflow"])


@router.post("/{service_name}/run", response_model=WorkflowResponse)
async def run_workflow(service_name: str, request: WorkflowRequest):
    """
    运行指定服务的工作流（非流式响应）
    
    Args:
        service_name: 服务名称，如coze_workflow等
        
    Returns:
        WorkflowResponse: 工作流运行结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到工作流服务: {service_name}")
    
    # 验证是否为工作流服务
    if service.service_type != "workflow":
        raise HTTPException(status_code=400, detail=f"服务 {service_name} 不是工作流服务")
    
    # 调用服务
    try:
        response = await service.chat_completion(
            message=request.message,
            conversation_id=request.conversation_id,
            **request.parameters
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工作流调用出错: {str(e)}")


@router.post("/{service_name}/stream")
async def stream_workflow(service_name: str, request: WorkflowRequest):
    """
    流式运行指定服务的工作流
    
    Args:
        service_name: 服务名称，如coze_workflow等
        
    Returns:
        StreamingResponse: 流式工作流运行结果
    """
    # 获取服务实例
    service = AIServiceRegistry.get_service(service_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"找不到工作流服务: {service_name}")
    
    # 验证是否为工作流服务
    if service.service_type != "workflow":
        raise HTTPException(status_code=400, detail=f"服务 {service_name} 不是工作流服务")
    
    # 生成事件流
    async def event_generator():
        try:
            async for chunk in service.stream_chat_completion(
                message=request.message,
                conversation_id=request.conversation_id,
                **request.parameters
            ):
                # 在API层将标准字典格式转换为SSE格式
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # 流结束标记
            yield "data: [DONE]\n\n"
        except Exception as e:
            # 出错时发送错误信息
            error_json = {"error": {"message": str(e)}}
            yield f"data: {json.dumps(error_json)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
