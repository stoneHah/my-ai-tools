"""
语音克隆服务注册表
管理所有语音克隆服务提供商
"""
import logging
from typing import Dict, Optional, Any

# 配置日志记录器
logger = logging.getLogger(__name__)

# 导入语音克隆服务
from ai_services.tts.cosyvoice_tts import register_cosyvoice_tts_service

# 全局语音克隆服务注册表
_voice_clone_services = {}

def register_all_voice_clone_services() -> Dict[str, Any]:
    """
    注册所有语音克隆服务
    
    Returns:
        已注册的语音克隆服务字典，键为服务名称
    """
    global _voice_clone_services
    
    # 注册阿里云CosyVoice语音克隆服务
    cosyvoice_service = register_cosyvoice_tts_service()
    if cosyvoice_service:
        _voice_clone_services[cosyvoice_service.service_name] = cosyvoice_service
        logger.info(f"已注册语音克隆服务: {cosyvoice_service.service_name}")
    
    # 在这里注册其他语音克隆服务
    # ...
    
    return _voice_clone_services

def get_voice_clone_service(service_name: str) -> Optional[Any]:
    """
    获取指定名称的语音克隆服务
    
    Args:
        service_name: 服务名称
        
    Returns:
        语音克隆服务实例，如果不存在则返回None
    """
    return _voice_clone_services.get(service_name)

def list_voice_clone_services() -> Dict[str, str]:
    """
    列出所有已注册的语音克隆服务
    
    Returns:
        语音克隆服务名称列表
    """
    return {name: service.service_type for name, service in _voice_clone_services.items()}
