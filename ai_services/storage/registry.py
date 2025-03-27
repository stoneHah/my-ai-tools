"""
对象存储服务注册表
管理所有对象存储服务提供商
"""
import logging
from typing import Dict, Optional, List, Type

from ai_services.storage.base import StorageServiceBase
from ai_services.storage.aliyun_oss import register_aliyun_oss_service

# 配置日志记录器
logger = logging.getLogger(__name__)


class StorageServiceRegistry:
    """对象存储服务注册表"""
    
    def __init__(self):
        """初始化注册表"""
        self.services: Dict[str, StorageServiceBase] = {}
    
    def register(self, service: StorageServiceBase) -> None:
        """
        注册存储服务
        
        Args:
            service: 存储服务实例
        """
        service_name = service.service_name
        if service_name in self.services:
            logger.warning(f"存储服务 '{service_name}' 已经注册，将被覆盖")
        
        self.services[service_name] = service
        logger.info(f"已注册存储服务: {service_name}")
    
    def get(self, service_name: str) -> Optional[StorageServiceBase]:
        """
        获取存储服务
        
        Args:
            service_name: 服务名称
            
        Returns:
            存储服务实例，如果不存在则返回None
        """
        return self.services.get(service_name)
    
    def list_services(self) -> List[str]:
        """
        列出所有注册的存储服务
        
        Returns:
            服务名称列表
        """
        return list(self.services.keys())


# 全局存储服务注册表实例
storage_service_registry = StorageServiceRegistry()


def register_all_storage_services() -> None:
    """注册所有存储服务"""
    # 注册阿里云OSS服务
    aliyun_oss_service = register_aliyun_oss_service()
    if aliyun_oss_service:
        storage_service_registry.register(aliyun_oss_service)
    
    # 在此处注册其他存储服务
    # ...
    
    logger.info(f"已注册 {len(storage_service_registry.list_services())} 个存储服务")


def get_storage_service(service_name: str = "aliyun") -> Optional[StorageServiceBase]:
    """
    获取存储服务
    
    Args:
        service_name: 服务名称，默认为"aliyun"
        
    Returns:
        存储服务实例，如果不存在则返回None
    """
    return storage_service_registry.get(service_name)
