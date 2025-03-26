"""
阿里云百炼 Qwen Audio ASR 服务实现
"""
import os
import logging
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
import asyncio
import json

import dashscope

from ai_services.asr.base import ASRServiceBase
from ai_services.asr.constants import SERVICE_TYPE, SERVICE_NAME_QWEN_AUDIO_ASR

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DashScopeASRService(ASRServiceBase):
    """阿里云百炼语音识别服务"""
    
    def __init__(self):
        """初始化服务"""
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            logger.warning("未设置DASHSCOPE_API_KEY环境变量")
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return SERVICE_NAME_QWEN_AUDIO_ASR
    
    @property
    def service_type(self) -> str:
        """服务类型"""
        return SERVICE_TYPE
    
    async def recognize_url(self, audio_url: str, **kwargs) -> Dict[str, Any]:
        """
        通过URL进行语音识别
        
        Args:
            audio_url: 音频URL
            **kwargs: 其他参数
            
        Returns:
            识别结果
        """
        try:
            logger.info(f"开始识别音频URL: {audio_url}")
            
            # 设置请求参数
            model = kwargs.get("model", "qwen-audio-turbo")
            
            # 调用DashScope API
            response = dashscope.audio.recognition.call(
                model=model,
                audio_url=audio_url,
                api_key=self.api_key
            )
            
            # 处理响应
            if response.status_code == 200:
                result = {
                    "id": str(uuid.uuid4()),
                    "text": response.output.text,
                    "status": "success"
                }
                logger.info(f"音频识别成功: {result['text'][:30]}...")
                return result
            else:
                error_msg = f"音频识别失败: {response.code}, {response.message}"
                logger.error(error_msg)
                return {
                    "id": str(uuid.uuid4()),
                    "text": "",
                    "status": "error",
                    "error": error_msg
                }
        except Exception as e:
            error_msg = f"音频识别异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "id": str(uuid.uuid4()),
                "text": "",
                "status": "error",
                "error": error_msg
            }
    
    async def recognize_file(self, audio_file_path: str, **kwargs) -> Dict[str, Any]:
        """
        通过本地文件进行语音识别
        
        Args:
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Returns:
            识别结果
        """
        try:
            logger.info(f"开始识别音频文件: {audio_file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(audio_file_path):
                error_msg = f"音频文件不存在: {audio_file_path}"
                logger.error(error_msg)
                return {
                    "id": str(uuid.uuid4()),
                    "text": "",
                    "status": "error",
                    "error": error_msg
                }
            
            # 设置请求参数
            model = kwargs.get("model", "qwen-audio-turbo")
            
            # 调用DashScope API
            with open(audio_file_path, 'rb') as f:
                response = dashscope.audio.recognition.call(
                    model=model,
                    audio_file=f,
                    api_key=self.api_key
                )
            
            # 处理响应
            if response.status_code == 200:
                result = {
                    "id": str(uuid.uuid4()),
                    "text": response.output.text,
                    "status": "success"
                }
                logger.info(f"音频识别成功: {result['text'][:30]}...")
                return result
            else:
                error_msg = f"音频识别失败: {response.code}, {response.message}"
                logger.error(error_msg)
                return {
                    "id": str(uuid.uuid4()),
                    "text": "",
                    "status": "error",
                    "error": error_msg
                }
        except Exception as e:
            error_msg = f"音频识别异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "id": str(uuid.uuid4()),
                "text": "",
                "status": "error",
                "error": error_msg
            }
    
    async def recognize(self, 
                       audio_url: Optional[str] = None,
                       audio_file_path: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        语音识别（兼容旧接口）
        
        Args:
            audio_url: 音频URL
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Returns:
            识别结果
        """
        return await super().recognize(audio_url, audio_file_path, **kwargs)
    
    async def stream_recognize_url(self, audio_url: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        通过URL进行流式语音识别
        
        Args:
            audio_url: 音频URL
            **kwargs: 其他参数
            
        Yields:
            流式识别结果
        """
        try:
            logger.info(f"开始流式识别音频URL: {audio_url}")
            
            # 设置请求参数
            model = kwargs.get("model", "qwen-audio-turbo")
            
            # 创建响应ID
            response_id = str(uuid.uuid4())
            
            # 模拟流式响应（DashScope目前不支持真正的流式识别）
            # 先获取完整识别结果
            full_result = await self.recognize_url(audio_url, **kwargs)
            
            if full_result["status"] == "error":
                yield full_result
                return
            
            # 将完整结果分段返回，模拟流式效果
            text = full_result["text"]
            # 按标点符号分段
            segments = []
            current_segment = ""
            
            for char in text:
                current_segment += char
                if char in "，。！？,.!?":
                    if current_segment.strip():
                        segments.append(current_segment)
                    current_segment = ""
            
            if current_segment.strip():
                segments.append(current_segment)
            
            # 如果没有合适的分段，就按字符返回
            if not segments:
                segments = [text[i:i+5] for i in range(0, len(text), 5)]
            
            # 返回流式结果
            accumulated_text = ""
            for i, segment in enumerate(segments):
                accumulated_text += segment
                yield {
                    "id": response_id,
                    "text": accumulated_text,
                    "delta": segment,
                    "status": "success",
                    "is_final": i == len(segments) - 1
                }
                # 模拟处理延迟
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_msg = f"流式音频识别异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                "id": str(uuid.uuid4()),
                "text": "",
                "delta": "",
                "status": "error",
                "error": error_msg,
                "is_final": True
            }
    
    async def stream_recognize_file(self, audio_file_path: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        通过本地文件进行流式语音识别
        
        Args:
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Yields:
            流式识别结果
        """
        try:
            logger.info(f"开始流式识别音频文件: {audio_file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(audio_file_path):
                error_msg = f"音频文件不存在: {audio_file_path}"
                logger.error(error_msg)
                yield {
                    "id": str(uuid.uuid4()),
                    "text": "",
                    "delta": "",
                    "status": "error",
                    "error": error_msg,
                    "is_final": True
                }
                return
            
            # 创建响应ID
            response_id = str(uuid.uuid4())
            
            # 模拟流式响应（DashScope目前不支持真正的流式识别）
            # 先获取完整识别结果
            full_result = await self.recognize_file(audio_file_path, **kwargs)
            
            if full_result["status"] == "error":
                yield full_result
                return
            
            # 将完整结果分段返回，模拟流式效果
            text = full_result["text"]
            # 按标点符号分段
            segments = []
            current_segment = ""
            
            for char in text:
                current_segment += char
                if char in "，。！？,.!?":
                    if current_segment.strip():
                        segments.append(current_segment)
                    current_segment = ""
            
            if current_segment.strip():
                segments.append(current_segment)
            
            # 如果没有合适的分段，就按字符返回
            if not segments:
                segments = [text[i:i+5] for i in range(0, len(text), 5)]
            
            # 返回流式结果
            accumulated_text = ""
            for i, segment in enumerate(segments):
                accumulated_text += segment
                yield {
                    "id": response_id,
                    "text": accumulated_text,
                    "delta": segment,
                    "status": "success",
                    "is_final": i == len(segments) - 1
                }
                # 模拟处理延迟
                await asyncio.sleep(0.1)
                
        except Exception as e:
            error_msg = f"流式音频识别异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                "id": str(uuid.uuid4()),
                "text": "",
                "delta": "",
                "status": "error",
                "error": error_msg,
                "is_final": True
            }
    
    async def stream_recognize(self, 
                              audio_url: Optional[str] = None,
                              audio_file_path: Optional[str] = None,
                              **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式语音识别（兼容旧接口）
        
        Args:
            audio_url: 音频URL
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Yields:
            识别结果片段
        """
        async for chunk in super().stream_recognize(audio_url, audio_file_path, **kwargs):
            yield chunk
