"""
对象存储服务模块
"""
from ai_services.storage.base import StorageServiceBase
from ai_services.storage.aliyun_oss import AliyunOSSService, register_aliyun_oss_service

__all__ = [
    "StorageServiceBase",
    "AliyunOSSService",
    "register_aliyun_oss_service"
]
