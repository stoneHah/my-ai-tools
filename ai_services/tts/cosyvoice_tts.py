"""
阿里云CosyVoice语音克隆服务实现
基于阿里云百炼平台的语音克隆服务
"""
import os
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, BinaryIO, List
import dashscope
from dashscope.audio.tts import TTSGenerator

from ai_services.tts.base import TTSServiceBase
from ai_services.tts.clone_base import VoiceCloneServiceBase
from ai_services.storage.registry import get_storage_service

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
                lambda: TTSGenerator.call(
                    model=params["model"],
                    text=params["text"],
                    voice_id=params["voice_id"],
                    format=params["format"],
                    sample_rate=params["sample_rate"],
                    speed_ratio=params["speed_ratio"],
                    volume_ratio=params["volume_ratio"],
                    pitch_ratio=params["pitch_ratio"],
                )
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"语音合成失败: {response.message}")
                raise Exception(f"语音合成失败: {response.message}")
            
            # 返回音频数据
            return response.get_audio_data()
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}", exc_info=True)
            raise
    
    async def stream_synthesize(self, text: str, voice_id: str, **kwargs) -> AsyncGenerator[bytes, None]:
        """
        流式将文本合成为语音
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数，如速度、音量、音调等
            
        Yields:
            流式合成的音频数据块
        """
        # 准备请求参数
        params = self._prepare_params(text, voice_id, **kwargs)
        
        try:
            # 调用阿里云CosyVoice API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: TTSGenerator.call(
                    model=params["model"],
                    text=params["text"],
                    voice_id=params["voice_id"],
                    format=params["format"],
                    sample_rate=params["sample_rate"],
                    speed_ratio=params["speed_ratio"],
                    volume_ratio=params["volume_ratio"],
                    pitch_ratio=params["pitch_ratio"],
                    stream=True,
                )
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"流式语音合成失败: {response.message}")
                raise Exception(f"流式语音合成失败: {response.message}")
            
            # 流式返回音频数据
            for chunk in response.get_audio_stream():
                yield chunk
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
        url = await storage_service.upload(object_key, audio_data, content_type=content_type)
        
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
            克隆任务信息
        """
        try:
            # 准备请求参数
            task_id = str(uuid.uuid4())
            
            # 调用阿里云CosyVoice克隆API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: dashscope.audio.tts.VoiceClone.call(
                    model="cosyvoice-clone-v1",
                    audio_url=sample_url,
                    voice_name=voice_name,
                    task_id=task_id
                )
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"创建克隆音色失败: {response.message}")
                raise Exception(f"创建克隆音色失败: {response.message}")
            
            # 返回任务信息
            result = {
                "task_id": task_id,
                "status": "pending",
                "message": "克隆任务已提交",
                "user_id": user_id,
                "app_id": app_id,
                "sample_url": sample_url,
                "voice_name": voice_name
            }
            
            return result
        except Exception as e:
            logger.error(f"创建克隆音色失败: {str(e)}", exc_info=True)
            raise
    
    async def query_clone_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        查询克隆任务状态
        
        Args:
            task_id: 任务ID
            **kwargs: 其他参数
            
        Returns:
            任务状态信息
        """
        try:
            # 调用阿里云CosyVoice查询API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: dashscope.audio.tts.VoiceClone.query(task_id=task_id)
            )
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"查询克隆任务失败: {response.message}")
                raise Exception(f"查询克隆任务失败: {response.message}")
            
            # 返回任务状态
            return {
                "task_id": task_id,
                "status": response.output.get("status", "unknown"),
                "message": response.output.get("message", ""),
                "voice_id": response.output.get("voice_id", ""),
                "created_at": response.output.get("created_at", ""),
                "updated_at": response.output.get("updated_at", "")
            }
        except Exception as e:
            logger.error(f"查询克隆任务失败: {str(e)}", exc_info=True)
            raise
    
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
        try:
            # 阿里云CosyVoice API暂不支持直接列出用户的克隆音色
            # 这里应该从数据库中获取用户的克隆音色列表
            # 此方法在实际应用中需要与数据库交互
            
            # 返回空列表，实际实现需要从数据库查询
            return []
        except Exception as e:
            logger.error(f"获取克隆音色列表失败: {str(e)}", exc_info=True)
            raise
    
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
        try:
            # 阿里云CosyVoice API暂不支持直接删除克隆音色
            # 这里应该在数据库中标记克隆音色为已删除
            # 此方法在实际应用中需要与数据库交互
            
            # 返回模拟的删除结果
            return {
                "voice_id": voice_id,
                "status": "deleted",
                "message": "克隆音色已删除"
            }
        except Exception as e:
            logger.error(f"删除克隆音色失败: {str(e)}", exc_info=True)
            raise
    
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
        try:
            # 阿里云CosyVoice API暂不支持直接更新克隆音色信息
            # 这里应该在数据库中更新克隆音色信息
            # 此方法在实际应用中需要与数据库交互
            
            # 返回模拟的更新结果
            return {
                "voice_id": voice_id,
                "status": "updated",
                "message": "克隆音色信息已更新"
            }
        except Exception as e:
            logger.error(f"更新克隆音色信息失败: {str(e)}", exc_info=True)
            raise
    
    def _prepare_params(self, text: str, voice_id: str, **kwargs) -> Dict[str, Any]:
        """
        准备API请求参数
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数
            
        Returns:
            请求参数字典
        """
        # 复制默认参数
        params = self.default_params.copy()
        
        # 更新基本参数
        params["text"] = text
        params["voice_id"] = voice_id
        
        # 更新可选参数
        if "format" in kwargs:
            params["format"] = kwargs["format"]
        
        if "sample_rate" in kwargs:
            params["sample_rate"] = kwargs["sample_rate"]
        
        if "speed" in kwargs:
            params["speed_ratio"] = float(kwargs["speed"])
        
        if "volume" in kwargs:
            params["volume_ratio"] = float(kwargs["volume"])
        
        if "pitch" in kwargs:
            params["pitch_ratio"] = float(kwargs["pitch"])
        
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
