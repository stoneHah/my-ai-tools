"""
工作流服务注册表
管理所有工作流服务提供商
"""
import logging
from typing import Dict, Optional, Any

# 配置日志记录器
logger = logging.getLogger(__name__)

# 导入工作流服务
from ai_services.workflow.coze import register_coze_workflow_service

# 全局工作流服务注册表
_workflow_services = {}

def register_all_workflow_services() -> Dict[str, Any]:
    """
    注册所有工作流服务
    
    Returns:
        已注册的工作流服务字典，键为服务名称
    """
    global _workflow_services
    
    # 注册Coze工作流服务
    coze_service = register_coze_workflow_service()
    if coze_service:
        _workflow_services[coze_service.service_name] = coze_service
        logger.info(f"已注册工作流服务: {coze_service.service_name}")
    
    # 在这里注册其他工作流服务
    # ...
    
    return _workflow_services

def get_workflow_service(service_name: str) -> Optional[Any]:
    """
    获取指定名称的工作流服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        工作流服务实例，如果不存在则返回None
    """
    return _workflow_services.get(service_name)

def list_workflow_services() -> Dict[str, str]:
    """
    列出所有已注册的工作流服务
    
    Returns:
        工作流服务名称和类型的字典
    """
    return {name: service.service_type for name, service in _workflow_services.items()}
