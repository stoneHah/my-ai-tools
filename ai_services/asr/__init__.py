"""
语音识别服务包
包含各种ASR服务实现
"""
from ai_services.asr.constants import *
from ai_services.asr.base import ASRServiceBase
from ai_services.asr.qwen_asr import DashScopeASRService
from ai_services.asr.paraformer_asr import DashScopeParaformerASRService
from ai_services.asr.registry import register_all_asr_services
