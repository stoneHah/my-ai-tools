"""
响应中间件
用于统一API响应格式
"""
import json
import logging
from typing import Callable, Dict, Any, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class APIResponseMiddleware(BaseHTTPMiddleware):
    """API响应中间件，统一包装响应格式"""
    
    def __init__(
        self, 
        app,
        exclude_paths: list = None,
        exclude_content_types: list = None
    ):
        """
        初始化中间件
        
        Args:
            app: FastAPI应用实例
            exclude_paths: 排除的路径前缀列表，这些路径不会被包装
            exclude_content_types: 排除的内容类型列表，这些类型不会被包装
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/stream"]
        self.exclude_content_types = exclude_content_types or [
            "application/octet-stream", 
            "audio/", 
            "video/",
            "image/",
            "multipart/form-data"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和响应"""
        # 检查是否需要排除此路径
        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.exclude_paths):
            return await call_next(request)
        
        # 获取原始响应
        response = await call_next(request)
        
        # 检查是否需要排除此内容类型
        content_type = response.headers.get("content-type", "")
        if any(ct in content_type for ct in self.exclude_content_types):
            return response
        
        # 检查是否已经是流式响应
        if isinstance(response, StreamingResponse):
            return response
        
        # 处理错误响应
        if response.status_code >= 400:
            return self._wrap_error_response(response)
        
        # 处理成功响应
        return await self._wrap_success_response(response)
    
    async def _wrap_success_response(self, response: Response) -> JSONResponse:
        """包装成功响应"""
        try:
            # 获取原始响应内容
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # 如果响应为空，返回空数据
            if not body:
                wrapped = {
                    "code": response.status_code,
                    "data": None,
                    "message": "成功"
                }
            else:
                # 解析并包装响应
                try:
                    data = json.loads(body.decode())
                    wrapped = {
                        "code": response.status_code,
                        "data": data,
                        "message": "成功"
                    }
                except json.JSONDecodeError:
                    # 如果不是JSON格式，直接返回原始响应
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
            
            # 创建新的响应，不保留原始的Content-Length头
            headers = dict(response.headers)
            if "content-length" in headers:
                del headers["content-length"]
            
            # 创建新的响应
            return JSONResponse(
                content=wrapped,
                status_code=response.status_code,
                headers=headers
            )
        except Exception as e:
            logger.error(f"包装响应失败: {str(e)}", exc_info=True)
            # 如果包装失败，返回原始响应
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
    
    def _wrap_error_response(self, response: Response) -> JSONResponse:
        """包装错误响应"""
        try:
            # 获取错误详情
            status_code = response.status_code
            error_detail = "请求处理失败"
            
            # 尝试从响应中获取更详细的错误信息
            try:
                content = json.loads(response.body.decode())
                if isinstance(content, dict) and "detail" in content:
                    error_detail = content["detail"]
            except:
                pass
            
            # 创建包装的错误响应
            wrapped = {
                "code": status_code,
                "data": None,
                "message": error_detail
            }
            
            # 移除Content-Length头
            headers = dict(response.headers)
            if "content-length" in headers:
                del headers["content-length"]
            
            return JSONResponse(
                content=wrapped,
                status_code=status_code,
                headers=headers
            )
        except Exception as e:
            logger.error(f"包装错误响应失败: {str(e)}", exc_info=True)
            # 如果包装失败，返回原始响应
            return response


# 便捷函数，用于创建API响应
def api_response(
    data: Any = None, 
    code: int = 200, 
    message: str = "成功"
) -> Dict[str, Any]:
    """
    创建统一的API响应格式
    
    Args:
        data: 响应数据
        code: 状态码
        message: 响应消息
    
    Returns:
        包装后的响应字典
    """
    return {
        "code": code,
        "data": data,
        "message": message
    }
