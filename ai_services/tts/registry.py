"""
TTS服务注册表
管理所有TTS服务提供商
"""
import logging
from typing import Dict, Optional, Any

# 配置日志记录器
logger = logging.getLogger(__name__)

# 导入TTS服务
from ai_services.tts.volcengine_tts import register_volcengine_tts_service

# 全局TTS服务注册表
_tts_services = {}

def register_all_tts_services() -> Dict[str, Any]:
    """
    注册所有TTS服务
    
    Returns:
        已注册的TTS服务字典，键为服务名称
    """
    global _tts_services
    
    # 注册火山引擎TTS服务
    volcengine_service = register_volcengine_tts_service()
    if volcengine_service:
        _tts_services[volcengine_service.service_name] = volcengine_service
        logger.info(f"已注册TTS服务: {volcengine_service.service_name}")
    
    # 在这里注册其他TTS服务
    # ...
    
    return _tts_services

def get_tts_service(service_name: str) -> Optional[Any]:
    """
    获取指定名称的TTS服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        TTS服务实例，如果不存在则返回None
    """
    return _tts_services.get(service_name)

def list_tts_services() -> Dict[str, str]:
    """
    列出所有已注册的TTS服务
    
    Returns:
        TTS服务名称列表
    """
    return {name: service.service_type for name, service in _tts_services.items()}
