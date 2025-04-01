"""
阿里云CosyVoice语音克隆服务实现
基于阿里云百炼平台的语音克隆服务
"""
import asyncio
import json
import logging
import os
import random
import string
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator

import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from ai_services.storage.registry import get_storage_service

from ai_services.tts.base import TTSServiceBase
from ai_services.tts.clone_base import VoiceCloneServiceBase

# 配置日志记录器
logger = logging.getLogger(__name__)

class CosyVoiceTTSService(TTSServiceBase, VoiceCloneServiceBase):
    """阿里云CosyVoice语音克隆服务实现"""
    
    def __init__(self, api_key: str, api_base: Optional[str] = None):
        """
        初始化阿里云CosyVoice语音克隆服务
        
        Args:
            api_key: 阿里云API密钥
            api_base: API基础URL，可选
        """
        self.api_key = api_key
        self.api_base = api_base
        
        # 设置DashScope API密钥
        dashscope.api_key = self.api_key
        
        # 默认参数
        self.default_params = {
            "model": "cosyvoice-v1",
            "format": "mp3",
            "sample_rate": 24000,
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        }
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "cosyvoice"

    @property
    def service_type(self) -> str:
        """服务类型"""
        return "tts"
    
    @property
    def clone_service_type(self) -> str:
        """克隆服务类型"""
        return "voice-clone"
    
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        """
        将文本合成为语音
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数，如速度、音量、音调等
            
        Returns:
            合成的音频数据
        """
        # 准备请求参数
        params = self._prepare_params(text, voice_id, **kwargs)
        
        try:
            # 调用阿里云CosyVoice API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: SpeechSynthesizer(
                    model=params["model"],
                    voice=params["voice_id"]
                ).call(
                    text=params["text"]
                )
            )
            
            # 返回音频数据
            return response
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}", exc_info=True)
            raise
    
    async def stream_synthesize(self, text: str, voice_id: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """
        将文本合成为语音（流式）
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数，如速度、音量、音调等
            
        Returns:
            合成的音频数据流
        """
        # 准备请求参数
        params = self._prepare_params(text, voice_id, **kwargs)
        
        try:
            # 调用阿里云CosyVoice API
            loop = asyncio.get_event_loop()
            synthesizer = SpeechSynthesizer(
                model=params["model"],
                voice=params["voice_id"]
            )
            
            # 同步调用，然后分块返回
            response = await loop.run_in_executor(
                None,
                lambda: synthesizer.call(
                    text=params["text"],
                )
            )
            
            # 将音频数据分块返回
            chunk_size = 4096  # 4KB 块大小
            audio_data = response
            
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i:i+chunk_size]
                
        except Exception as e:
            logger.error(f"流式语音合成失败: {str(e)}", exc_info=True)
            raise
    
    async def save_to_file(self, text: str, voice_id: str, output_path: str, **kwargs) -> str:
        """
        将文本合成为语音并保存到文件
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            output_path: 输出文件路径
            **kwargs: 其他参数，如速度、音量、音调等
            
        Returns:
            保存的文件路径
        """
        # 获取合成的音频数据
        audio_data = await self.synthesize(text, voice_id, **kwargs)
        
        # 保存到文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        return output_path
    
    async def save_to_oss(self, text: str, voice_id: str, object_key: str, oss_provider: str = "aliyun", **kwargs) -> str:
        """
        将文本合成为语音并保存到对象存储服务(OSS)
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            object_key: OSS对象键名/路径
            oss_provider: OSS提供商，默认为"aliyun"
            **kwargs: 其他参数，如速度、音量、音调等
            
        Returns:
            OSS中的对象URL
        """
        # 获取合成的音频数据
        audio_data = await self.synthesize(text, voice_id, **kwargs)
        
        # 获取存储服务
        storage_service = get_storage_service(oss_provider)
        if not storage_service:
            raise Exception(f"找不到存储服务: {oss_provider}")
        
        # 上传到OSS
        content_type = "audio/mpeg" if kwargs.get("format", "mp3") == "mp3" else "audio/wav"
        url = await storage_service.upload_data(audio_data, object_key, content_type=content_type)
        
        return url
    
    async def create_clone_voice(self, sample_url: str, voice_name: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        创建克隆音色
        
        Args:
            sample_url: 样本音频URL
            voice_name: 音色名称
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            克隆音色信息，包含voice_id
        """
        try:
            # 创建VoiceEnrollmentService实例
            voice_service = VoiceEnrollmentService(api_key=self.api_key)
            
            # 生成随机前缀，由数字和小写字母组成，长度小于10个字符
            random_prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            prefix = kwargs.get("prefix") or random_prefix
            
            # 调用VoiceEnrollmentService的create_voice方法
            loop = asyncio.get_event_loop()
            voice_id = await loop.run_in_executor(
                None,
                lambda: voice_service.create_voice(
                    target_model="cosyvoice-clone-v1",
                    prefix=prefix,
                    url=sample_url
                )
            )
            
            # 检查响应
            if not voice_id:
                raise Exception("创建克隆音色失败: 没有返回voice_id")
            
            # 构建结果
            result = {
                "voice_id": voice_id,
                "task_id": voice_id,  # 使用voice_id作为task_id
                "status": "success",
                "message": "克隆音色创建成功",
                "user_id": user_id,
                "app_id": app_id,
                "sample_url": sample_url,
                "voice_name": voice_name,
                "created_at": datetime.now().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"创建克隆音色失败: {str(e)}", exc_info=True)
            raise Exception(f"创建克隆音色失败: {str(e)}")
    
    async def query_clone_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        查询克隆任务状态
        
        Args:
            task_id: 任务ID
            **kwargs: 其他参数
            
        Returns:
            任务状态信息
        """
        # CosyVoice不需要查询任务状态，因为创建克隆音色是同步的
        # 返回一个固定的成功状态
        return {
            "task_id": task_id,
            "status": "success",
            "voice_id": task_id
        }
    
    async def list_clone_voices(self, user_id: str, app_id: str, **kwargs) -> List[Dict[str, Any]]:
        """
        获取用户的克隆音色列表
        
        Args:
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            克隆音色列表
        """
        # 阿里云CosyVoice API暂不支持直接列出用户的克隆音色
        # 这里应该从数据库中获取用户的克隆音色列表
        # 此方法在实际应用中需要与数据库交互
            
        # 返回空列表，实际实现需要从数据库查询
        return []
    
    async def get_clone_voice(self, voice_id: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        获取克隆音色信息
        
        Args:
            voice_id: 音色ID
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            克隆音色信息
        """
        # 阿里云CosyVoice API暂不支持直接获取克隆音色信息
        # 这里应该从数据库中获取克隆音色信息
        # 此方法在实际应用中需要与数据库交互
            
        # 返回模拟的克隆音色信息
        return {
            "voice_id": voice_id,
            "user_id": user_id,
            "app_id": app_id,
            "name": kwargs.get("name", "Unknown"),
            "platform": "cosyvoice"
        }
    
    async def delete_clone_voice(self, voice_id: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        删除克隆音色
        
        Args:
            voice_id: 音色ID
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数
            
        Returns:
            删除结果
        """
        # 阿里云CosyVoice API暂不支持直接删除克隆音色
        # 这里应该在数据库中标记克隆音色为已删除
        # 此方法在实际应用中需要与数据库交互
            
        # 返回模拟的删除结果
        return {
            "voice_id": voice_id,
            "status": "success",
            "message": "删除成功"
        }
    
    async def update_clone_voice(self, voice_id: str, user_id: str, app_id: str, **kwargs) -> Dict[str, Any]:
        """
        更新克隆音色信息
        
        Args:
            voice_id: 音色ID
            user_id: 用户ID
            app_id: 应用ID
            **kwargs: 其他参数，如name、description等
            
        Returns:
            更新结果
        """
        # 阿里云CosyVoice API暂不支持直接更新克隆音色信息
        # 这里应该在数据库中更新克隆音色信息
        # 此方法在实际应用中需要与数据库交互
            
        # 返回模拟的更新结果
        return {
            "voice_id": voice_id,
            "status": "success",
            "message": "更新成功",
            "updated_fields": list(kwargs.keys())
        }
    
    def _prepare_params(self, text: str, voice_id: str, **kwargs) -> Dict[str, Any]:
        """
        u51c6u5907APIu8bf7u6c42u53c2u6570
        
        Args:
            text: u8981u5408u6210u7684u6587u672c
            voice_id: u97f3u8272ID
            **kwargs: u5176u4ed6u53c2u6570
            
        Returns:
            u8bf7u6c42u53c2u6570u5b57u5178
        """
        # u590du5236u9ed8u8ba4u53c2u6570
        params = self.default_params.copy()
        
        # u66f4u65b0u57fau672cu53c2u6570
        params["text"] = text
        params["voice_id"] = voice_id
        
        # u8bbeu7f6eu9ed8u8ba4u503c
        params["format"] = kwargs.get("format", "mp3")
        params["sample_rate"] = kwargs.get("sample_rate", 24000)
        params["speed_ratio"] = float(kwargs.get("speed", 1.0))
        params["volume_ratio"] = float(kwargs.get("volume", 1.0))
        params["pitch_ratio"] = float(kwargs.get("pitch", 1.0))
        
        return params


def register_cosyvoice_tts_service() -> Optional[CosyVoiceTTSService]:
    """
    注册阿里云CosyVoice语音克隆服务
    
    Returns:
        阿里云CosyVoice语音克隆服务实例，如果缺少必要的环境变量则返回None
    """
    # 从环境变量获取API密钥
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        logger.warning("缺少DASHSCOPE_API_KEY环境变量，无法初始化阿里云CosyVoice语音克隆服务")
        return None
    
    # 从环境变量获取API基础URL（可选）
    api_base = os.environ.get("DASHSCOPE_API_BASE")
    
    # 创建并返回服务实例
    return CosyVoiceTTSService(api_key=api_key, api_base=api_base)
