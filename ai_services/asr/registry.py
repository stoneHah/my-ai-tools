"""
ASR服务注册模块
"""
import os
import logging
from typing import Dict, Any, Optional

from ai_services.base import AIServiceRegistry
from ai_services.asr.base import ASRServiceBase
from ai_services.asr.qwen_asr import DashScopeASRService
from ai_services.asr.paraformer_asr import DashScopeParaformerASRService

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def register_qwen_asr_service() -> Optional[DashScopeASRService]:
    """
    注册阿里云百炼 Qwen Audio ASR 服务
    
    Returns:
        DashScopeASRService: 服务实例，如果注册失败则返回None
    """
    try:
        # 创建服务实例
        service = DashScopeASRService()
        
        # 注册服务
        AIServiceRegistry.register(service)
        
        logger.info(f"已注册服务: {service.service_name} (类型: {service.service_type})")
        return service
    except Exception as e:
        logger.error(f"注册 Qwen Audio ASR 服务失败: {str(e)}", exc_info=True)
        return None


def register_paraformer_asr_service() -> Optional[DashScopeParaformerASRService]:
    """
    注册阿里云百炼 Paraformer ASR 服务
    
    Returns:
        DashScopeParaformerASRService: 服务实例，如果注册失败则返回None
    """
    try:
        # 创建服务实例
        service = DashScopeParaformerASRService()
        
        # 注册服务
        AIServiceRegistry.register(service)
        
        logger.info(f"已注册服务: {service.service_name} (类型: {service.service_type})")
        return service
    except Exception as e:
        logger.error(f"注册 Paraformer ASR 服务失败: {str(e)}", exc_info=True)
        return None


def register_all_asr_services() -> Dict[str, Any]:
    """
    注册所有 ASR 服务
    
    Returns:
        Dict[str, Any]: 注册结果，包含成功注册的服务
    """
    services = {}
    
    # 注册 Qwen Audio ASR 服务
    qwen_service = register_qwen_asr_service()
    if qwen_service:
        services["qwen"] = qwen_service
    
    # 注册 Paraformer ASR 服务
    paraformer_service = register_paraformer_asr_service()
    if paraformer_service:
        services["paraformer"] = paraformer_service
    
    return services
