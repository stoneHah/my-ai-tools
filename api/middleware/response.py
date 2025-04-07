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
            error_data = None
            
            # 尝试从响应中获取更详细的错误信息
            try:
                content = json.loads(response.body.decode())
                if isinstance(content, dict):
                    # 优先使用detail字段
                    if "detail" in content:
                        error_detail = content["detail"]
                    # 如果有message字段，使用message字段
                    elif "message" in content:
                        error_detail = content["message"]
                    # 如果有error字段，使用error字段
                    elif "error" in content:
                        error_detail = content["error"]
                    # 如果有错误描述字段，使用错误描述
                    elif "error_description" in content:
                        error_detail = content["error_description"]
                    
                    # 保留原始错误数据，以便客户端可以获取更多信息
                    # 移除已经作为message使用的字段，避免重复
                    error_content = content.copy()
                    for field in ["detail", "message", "error", "error_description"]:
                        if field in error_content and error_content[field] == error_detail:
                            error_content.pop(field, None)
                    
                    # 如果还有其他错误信息，添加到data字段
                    if error_content and error_content != {}:
                        error_data = error_content
            except Exception as e:
                # 如果解析失败，记录错误但继续处理
                logger.debug(f"解析错误响应内容失败: {str(e)}")
                try:
                    # 尝试直接获取响应体作为错误信息
                    body_text = response.body.decode().strip()
                    if body_text and body_text != "":
                        error_detail = f"错误: {body_text}"
                except:
                    pass
            
            # 根据状态码添加更具体的错误类型描述
            error_type = self._get_error_type_by_status(status_code)
            if error_type and not error_detail.startswith(error_type):
                error_detail = f"{error_type}: {error_detail}"
            
            # 创建包装的错误响应
            wrapped = {
                "code": status_code,
                "data": error_data,
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
    
    def _get_error_type_by_status(self, status_code: int) -> str:
        """根据HTTP状态码获取错误类型描述"""
        error_types = {
            400: "请求参数错误",
            401: "未授权访问",
            403: "禁止访问",
            404: "资源不存在",
            405: "方法不允许",
            408: "请求超时",
            409: "资源冲突",
            413: "请求体过大",
            415: "不支持的媒体类型",
            422: "请求数据验证失败",
            429: "请求过于频繁",
            500: "服务器内部错误",
            501: "功能未实现",
            502: "网关错误",
            503: "服务不可用",
            504: "网关超时"
        }
        return error_types.get(status_code, "")

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
