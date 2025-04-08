"""
异常处理中间件
用于统一捕获和处理业务异常
"""
import logging
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.exceptions.business_exception import BusinessException

logger = logging.getLogger(__name__)


class BusinessExceptionMiddleware(BaseHTTPMiddleware):
    """业务异常处理中间件"""
    
    def __init__(self, app):
        """初始化中间件"""
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和捕获异常"""
        try:
            # 尝试处理请求
            return await call_next(request)
        except BusinessException as e:
            # 捕获业务异常
            logger.error(
                f"业务异常: {e.message} [错误码: {e.code}]",
                exc_info=True
            )
            
            # 返回业务异常响应，HTTP状态码固定为200
            return JSONResponse(
                status_code=200,  # 业务异常统一使用HTTP 200
                content=e.to_dict()
            )
        except StarletteHTTPException as e:
            # 捕获HTTP异常但不转换为业务异常
            logger.error(
                f"HTTP异常: {e.detail} [状态码: {e.status_code}]",
                exc_info=True
            )
            
            # 直接返回HTTP异常，保持原有状态码
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "code": e.status_code,
                    "message": str(e.detail),
                    "data": None
                }
            )
        except Exception as e:
            # 捕获其他未处理的异常（系统级异常）
            logger.error(
                f"系统异常: {str(e)}",
                exc_info=True
            )
            
            # 获取异常堆栈信息
            stack_trace = traceback.format_exc()
            
            # 系统级异常使用HTTP 500状态码
            return JSONResponse(
                status_code=500,  # 系统级异常使用HTTP 500
                content={
                    "code": 500,
                    "message": f"系统内部错误: {str(e)}",
                    "data": {"stack_trace": stack_trace}
                }
            )
