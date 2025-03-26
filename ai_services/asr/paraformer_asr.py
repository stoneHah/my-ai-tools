"""
阿里云百炼 Paraformer ASR 服务实现
"""
import os
import logging
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
import asyncio
import json
from urllib import request
from http import HTTPStatus

import dashscope

from dashscope.audio.asr import Recognition
from ai_services.asr.base import ASRServiceBase
from ai_services.asr.constants import SERVICE_TYPE, SERVICE_NAME_PARFORMER_V2

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DashScopeParaformerASRService(ASRServiceBase):
    """阿里云百炼Paraformer语音识别服务"""
    
    def __init__(self):
        """初始化服务"""
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            logger.warning("未设置DASHSCOPE_API_KEY环境变量")
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return SERVICE_NAME_PARFORMER_V2
    
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
            model = kwargs.get("model", "paraformer-v2")
            
            # 调用DashScope API
            response = dashscope.audio.transcription.call(
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
            
        # 获取音频文件的格式
        audio_file_format = audio_file_path.split('.')[-1]
        if audio_file_format not in ['wav', 'mp3', 'aac', 'pcm']:
            error_msg = f"不支持的音频文件格式: {audio_file_format}"
            logger.error(error_msg)
            return {
                "id": str(uuid.uuid4()),
                "text": "",
                "status": "error",
                "error": error_msg
            }
        
        sample_rate = kwargs.get("sample_rate", 16000)
        format = kwargs.get("format", audio_file_format)
        recognition = Recognition(model='paraformer-realtime-v2',
                        format=format,
                        sample_rate=sample_rate,
                        # “language_hints”只支持paraformer-v2和paraformer-realtime-v2模型
                        language_hints=['zh', 'en'],
                        callback=None)
        result = recognition.call(audio_file_path)
        sentence_list = result.get_sentence()
        if sentence_list is None:
            print('No result')
            print(result)
            return {
                "id": str(uuid.uuid4()),
                "text": "",
                "status": "error",
                "error": "No result"
            }
        else:
            result_text = ''.join([sentence['text'] for sentence in sentence_list])
            return {
                "id": str(uuid.uuid4()),
                "text": result_text,
                "status": "success"
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
            model = kwargs.get("model", "paraformer-v2")
            
            # 创建响应ID
            response_id = str(uuid.uuid4())
            
            # 下载音频文件
            audio_data = None
            try:
                with request.urlopen(audio_url) as response:
                    if response.status == HTTPStatus.OK:
                        audio_data = response.read()
                    else:
                        error_msg = f"下载音频文件失败: HTTP状态码 {response.status}"
                        logger.error(error_msg)
                        yield {
                            "id": response_id,
                            "text": "",
                            "delta": "",
                            "status": "error",
                            "error": error_msg,
                            "is_final": True
                        }
                        return
            except Exception as e:
                error_msg = f"下载音频文件异常: {str(e)}"
                logger.error(error_msg, exc_info=True)
                yield {
                    "id": response_id,
                    "text": "",
                    "delta": "",
                    "status": "error",
                    "error": error_msg,
                    "is_final": True
                }
                return
            
            # 调用流式识别API
            response = dashscope.audio.transcription.call(
                model=model,
                audio_content=audio_data,
                api_key=self.api_key,
                streaming=True
            )
            
            # 处理流式响应
            accumulated_text = ""
            for event in response.events():
                if event.event == 'transcription':
                    # 获取当前文本片段
                    segment = event.output.text
                    accumulated_text += segment
                    
                    yield {
                        "id": response_id,
                        "text": accumulated_text,
                        "delta": segment,
                        "status": "success",
                        "is_final": False
                    }
                elif event.event == 'end':
                    # 最终结果
                    yield {
                        "id": response_id,
                        "text": accumulated_text,
                        "delta": "",
                        "status": "success",
                        "is_final": True
                    }
                elif event.event == 'error':
                    # 错误
                    error_msg = f"流式识别错误: {event.message}"
                    logger.error(error_msg)
                    yield {
                        "id": response_id,
                        "text": accumulated_text,
                        "delta": "",
                        "status": "error",
                        "error": error_msg,
                        "is_final": True
                    }
                    
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
            
            # 设置请求参数
            model = kwargs.get("model", "paraformer-v2")
            response_id = str(uuid.uuid4())
            
            # 读取音频文件
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # 调用流式识别API
            response = dashscope.audio.transcription.call(
                model=model,
                audio_content=audio_data,
                api_key=self.api_key,
                streaming=True
            )
            
            # 处理流式响应
            accumulated_text = ""
            for event in response.events():
                if event.event == 'transcription':
                    # 获取当前文本片段
                    segment = event.output.text
                    accumulated_text += segment
                    
                    yield {
                        "id": response_id,
                        "text": accumulated_text,
                        "delta": segment,
                        "status": "success",
                        "is_final": False
                    }
                elif event.event == 'end':
                    # 最终结果
                    yield {
                        "id": response_id,
                        "text": accumulated_text,
                        "delta": "",
                        "status": "success",
                        "is_final": True
                    }
                elif event.event == 'error':
                    # 错误
                    error_msg = f"流式识别错误: {event.message}"
                    logger.error(error_msg)
                    yield {
                        "id": response_id,
                        "text": accumulated_text,
                        "delta": "",
                        "status": "error",
                        "error": error_msg,
                        "is_final": True
                    }
                    
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
