"""
业务异常模块
定义统一的业务异常类及错误码
"""
from typing import Any, Dict, Optional, Type


class BusinessException(Exception):
    """
    业务异常基类
    用于替代直接抛出HTTPException，提供更丰富的错误信息
    """
    def __init__(
        self,
        code: int,
        message: str,
        data: Any = None,
        exception: Exception = None
    ):
        """
        初始化业务异常
        
        Args:
            code: 业务错误码
            message: 错误消息
            data: 附加错误数据
            exception: 原始异常对象
        """
        self.code = code
        self.message = message
        self.data = data
        self.exception = exception
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典，用于API响应
        """
        result = {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }
        
        # 如果有原始异常，添加异常信息
        if self.exception and isinstance(self.exception, Exception):
            # 只在非生产环境添加详细的异常信息
            exception_info = {
                "type": self.exception.__class__.__name__,
                "message": str(self.exception)
            }
            
            # 如果data为None，直接设置为异常信息
            if self.data is None:
                result["data"] = exception_info
            # 如果data是字典，添加异常信息
            elif isinstance(self.data, dict):
                result["data"]["exception"] = exception_info
            # 其他情况，创建一个包含原始data和异常信息的新字典
            else:
                result["data"] = {
                    "original_data": self.data,
                    "exception": exception_info
                }
                
        return result


# 预定义的业务错误码
class ErrorCode:
    """业务错误码定义"""
    # 通用错误 (1000-1999)
    GENERAL_ERROR = 1000
    PARAM_ERROR = 1001
    NOT_FOUND = 1002
    UNAUTHORIZED = 1003
    FORBIDDEN = 1004
    VALIDATION_ERROR = 1005
    RATE_LIMIT = 1006
    
    # AI服务错误 (2000-2999)
    AI_SERVICE_ERROR = 2000
    AI_SERVICE_NOT_FOUND = 2001
    AI_SERVICE_UNAVAILABLE = 2002
    AI_REQUEST_ERROR = 2003
    AI_RESPONSE_ERROR = 2004
    
    # 语音服务错误 (3000-3999)
    ASR_ERROR = 3000
    TTS_ERROR = 3100
    VOICE_CLONE_ERROR = 3200
    
    # 存储服务错误 (4000-4999)
    STORAGE_ERROR = 4000
    FILE_NOT_FOUND = 4001
    UPLOAD_ERROR = 4002
    DOWNLOAD_ERROR = 4003
    
    # 数据库错误 (5000-5999)
    DB_ERROR = 5000
    DB_CONNECTION_ERROR = 5001
    DB_QUERY_ERROR = 5002
    DB_TRANSACTION_ERROR = 5003
    
    # 外部服务错误 (6000-6999)
    EXTERNAL_SERVICE_ERROR = 6000
    EXTERNAL_SERVICE_UNAVAILABLE = 6001
    EXTERNAL_REQUEST_ERROR = 6002
    EXTERNAL_RESPONSE_ERROR = 6003


# 常用业务异常类
class ParameterError(BusinessException):
    """参数错误异常"""
    def __init__(self, message: str = "参数错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.PARAM_ERROR,
            message=message,
            data=data,
            exception=exception
        )


class NotFoundError(BusinessException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            data=data,
            exception=exception
        )


class UnauthorizedError(BusinessException):
    """未授权异常"""
    def __init__(self, message: str = "未授权访问", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            data=data,
            exception=exception
        )


class ForbiddenError(BusinessException):
    """禁止访问异常"""
    def __init__(self, message: str = "禁止访问", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.FORBIDDEN,
            message=message,
            data=data,
            exception=exception
        )


class ValidationError(BusinessException):
    """数据验证错误异常"""
    def __init__(self, message: str = "数据验证失败", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            data=data,
            exception=exception
        )


class AIServiceError(BusinessException):
    """AI服务错误异常"""
    def __init__(self, message: str = "AI服务错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.AI_SERVICE_ERROR,
            message=message,
            data=data,
            exception=exception
        )


class StorageError(BusinessException):
    """存储服务错误异常"""
    def __init__(self, message: str = "存储服务错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.STORAGE_ERROR,
            message=message,
            data=data,
            exception=exception
        )


class DatabaseError(BusinessException):
    """数据库错误异常"""
    def __init__(self, message: str = "数据库错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.DB_ERROR,
            message=message,
            data=data,
            exception=exception
        )


class ExternalServiceError(BusinessException):
    """外部服务错误异常"""
    def __init__(self, message: str = "外部服务错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=message,
            data=data,
            exception=exception
        )
