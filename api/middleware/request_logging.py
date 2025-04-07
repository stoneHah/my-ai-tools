"""
请求日志中间件
"""
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import StreamingResponse

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
        
        # 记录响应状态码
        status_code = response.status_code
        
        # 对于错误响应，尝试记录详细信息
        if status_code >= 400:
            try:
                # 对于流式响应，不尝试读取响应体
                if isinstance(response, StreamingResponse):
                    logger.error(f"Response {status_code} {method} {path} (Streaming response)")
                else:
                    # 保存原始响应体
                    body = b""
                    # 创建一个新的异步迭代器来读取响应体
                    original_body_iterator = response.body_iterator
                    
                    # 如果响应体迭代器不是异步迭代器，则不尝试读取
                    if hasattr(original_body_iterator, "__aiter__"):
                        async for chunk in original_body_iterator:
                            body += chunk
                        
                        # 创建一个新的异步迭代器
                        async def new_body_iterator():
                            yield body
                        
                        response.body_iterator = new_body_iterator()
                        
                        # 尝试解析响应体以获取详细错误信息
                        try:
                            content = json.loads(body.decode())
                            if isinstance(content, dict) and "detail" in content:
                                logger.error(f"Response {status_code} {method} {path}\nError detail: {content['detail']}")
                            else:
                                logger.error(f"Response {status_code} {method} {path}\nBody: {json.dumps(content, ensure_ascii=False, indent=2)}")
                        except json.JSONDecodeError:
                            # 如果不是JSON格式，直接记录原始响应体
                            logger.error(f"Response {status_code} {method} {path}\nBody: {body.decode()}")
                    else:
                        logger.error(f"Response {status_code} {method} {path} (Non-async body iterator)")
            except Exception as e:
                logger.error(f"Response {status_code} {method} {path}\nFailed to log response body: {str(e)}")
        else:
            logger.info(f"Response {status_code} {method} {path}")
            
        return response
