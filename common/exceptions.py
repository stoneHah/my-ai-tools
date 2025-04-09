"""
异常定义模块
"""
from typing import Optional, Dict, Any


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
    
    # 媒体处理错误 (7000-7999)
    MEDIA_PROCESSING_ERROR = 7000
    
    # 任务相关错误 (8000-8999)
    TASK_ERROR = 8000
    TASK_NOT_FOUND = 8001
    TASK_FAILED = 8002
    TASK_TIMEOUT = 8003


class BusinessException(Exception):
    """业务异常基类"""
    
    def __init__(self, 
                code: str = None, 
                message: str = None,
                details: Optional[Dict[str, Any]] = None,
                error_code: int = None,
                data: Any = None,
                exception: Exception = None):
        """
        初始化业务异常
        
        Args:
            code: 错误代码字符串
            message: 错误消息
            details: 错误详情
            error_code: 错误代码数字（兼容旧版）
            data: 附加错误数据（兼容旧版）
            exception: 原始异常对象（兼容旧版）
        """
        self.code = code or "BUSINESS_ERROR"
        self.message = message or "业务异常"
        self.details = details or {}
        self.error_code = error_code or ErrorCode.GENERAL_ERROR
        self.data = data
        self.exception = exception
        
        # 如果有原始异常，添加到details中
        if exception and isinstance(exception, Exception):
            self.details["exception"] = {
                "type": exception.__class__.__name__,
                "message": str(exception)
            }
        
        # 如果有旧版data，添加到details中
        if data is not None and "data" not in self.details:
            self.details["data"] = data
            
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典
        
        Returns:
            异常字典
        """
        # 新版格式
        result = {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }
        
        # 兼容旧版格式
        if hasattr(self, 'error_code') and self.error_code is not None:
            result["error_code"] = self.error_code
            
        if hasattr(self, 'data') and self.data is not None:
            result["data"] = self.data
            
        return result


class ResourceNotFoundException(BusinessException):
    """资源未找到异常"""
    
    def __init__(self, 
                resource_type: str, 
                resource_id: str, 
                message: Optional[str] = None,
                details: Optional[Dict[str, Any]] = None):
        """
        初始化资源未找到异常
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            message: 错误消息
            details: 错误详情
        """
        if not message:
            message = f"{resource_type} with id '{resource_id}' not found"
        
        error_details = details or {}
        error_details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=message,
            details=error_details,
            error_code=ErrorCode.NOT_FOUND
        )


class InvalidParameterException(BusinessException):
    """参数无效异常"""
    
    def __init__(self, 
                parameter: str, 
                reason: str, 
                value: Optional[Any] = None,
                details: Optional[Dict[str, Any]] = None):
        """
        初始化参数无效异常
        
        Args:
            parameter: 参数名
            reason: 无效原因
            value: 参数值
            details: 错误详情
        """
        error_details = details or {}
        error_details.update({
            "parameter": parameter,
            "reason": reason
        })
        
        if value is not None:
            error_details["value"] = str(value)
        
        super().__init__(
            code="INVALID_PARAMETER",
            message=f"Parameter '{parameter}' is invalid: {reason}",
            details=error_details,
            error_code=ErrorCode.PARAM_ERROR
        )


class ServiceUnavailableException(BusinessException):
    """服务不可用异常"""
    
    def __init__(self, 
                service_name: str, 
                reason: str, 
                details: Optional[Dict[str, Any]] = None):
        """
        初始化服务不可用异常
        
        Args:
            service_name: 服务名称
            reason: 不可用原因
            details: 错误详情
        """
        error_details = details or {}
        error_details.update({
            "service_name": service_name,
            "reason": reason
        })
        
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"Service '{service_name}' is unavailable: {reason}",
            details=error_details,
            error_code=ErrorCode.AI_SERVICE_UNAVAILABLE
        )


class TaskFailedException(BusinessException):
    """任务失败异常"""
    
    def __init__(self, 
                task_id: str, 
                reason: str, 
                details: Optional[Dict[str, Any]] = None):
        """
        初始化任务失败异常
        
        Args:
            task_id: 任务ID
            reason: 失败原因
            details: 错误详情
        """
        error_details = details or {}
        error_details.update({
            "task_id": task_id,
            "reason": reason
        })
        
        super().__init__(
            code="TASK_FAILED",
            message=f"Task '{task_id}' failed: {reason}",
            details=error_details,
            error_code=ErrorCode.TASK_FAILED
        )


# 兼容旧版异常类
class ParameterError(BusinessException):
    """参数错误异常"""
    def __init__(self, message: str = "参数错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code="PARAM_ERROR",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.PARAM_ERROR
        )


class NotFoundError(BusinessException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在", data: Any = None, exception: Exception = None):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.NOT_FOUND
        )


class UnauthorizedError(BusinessException):
    """未授权异常"""
    def __init__(self, message: str = "未授权访问", data: Any = None, exception: Exception = None):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.UNAUTHORIZED
        )


class ForbiddenError(BusinessException):
    """禁止访问异常"""
    def __init__(self, message: str = "禁止访问", data: Any = None, exception: Exception = None):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.FORBIDDEN
        )


class ValidationError(BusinessException):
    """数据验证错误异常"""
    def __init__(self, message: str = "数据验证失败", data: Any = None, exception: Exception = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.VALIDATION_ERROR
        )


class AIServiceError(BusinessException):
    """AI服务错误异常"""
    def __init__(self, message: str = "AI服务错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code="AI_SERVICE_ERROR",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.AI_SERVICE_ERROR
        )


class StorageError(BusinessException):
    """存储服务错误异常"""
    def __init__(self, message: str = "存储服务错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code="STORAGE_ERROR",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.STORAGE_ERROR
        )


class ExternalServiceError(BusinessException):
    """外部服务错误异常"""
    def __init__(self, message: str = "外部服务错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
        )


class MediaProcessingError(BusinessException):
    """媒体处理错误异常"""
    def __init__(self, message: str = "媒体处理错误", data: Any = None, exception: Exception = None):
        super().__init__(
            code="MEDIA_PROCESSING_ERROR",
            message=message,
            data=data,
            exception=exception,
            error_code=ErrorCode.MEDIA_PROCESSING_ERROR
        )
