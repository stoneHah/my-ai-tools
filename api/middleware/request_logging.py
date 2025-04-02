"""
请求日志中间件
"""
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 记录请求路径和方法
        path = request.url.path
        method = request.method
        
        # 对于POST/PUT请求，记录请求体
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                logger.info(
                    f"Request {method} {path}\nBody: {json.dumps(body, ensure_ascii=False, indent=2)}"
                )
            except Exception as e:
                logger.info(f"Request {method} {path}\nBody: Could not parse JSON body: {str(e)}")
        else:
            # 对于其他请求，记录查询参数
            query_params = dict(request.query_params)
            if query_params:
                logger.info(
                    f"Request {method} {path}\nQuery params: {json.dumps(query_params, ensure_ascii=False, indent=2)}"
                )
            else:
                logger.info(f"Request {method} {path}")

        # 继续处理请求
        response = await call_next(request)
        return response
