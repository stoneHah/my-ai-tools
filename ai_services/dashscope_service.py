"""
阿里云百炼AI服务实现
提供基于阿里云百炼的AI服务实现
"""
import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
import asyncio

from dashscope import MultiModalConversation

from ai_services.base import ASRServiceBase, AIServiceRegistry

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志级别为INFO


class DashScopeASRService(ASRServiceBase):
    """阿里云百炼语音识别服务"""
    
    def __init__(self, api_key: str = None):
        """
        初始化服务
        
        Args:
            api_key: 阿里云百炼API密钥，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("必须提供DASHSCOPE_API_KEY")
        
        # 设置API密钥
        os.environ["DASHSCOPE_API_KEY"] = self.api_key
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "dashscope"
    
    @property
    def service_type(self) -> str:
        """服务类型"""
        return "asr"
    
    async def recognize(self, 
                       audio_url: Optional[str] = None,
                       audio_file_path: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        语音识别接口
        
        Args:
            audio_url: 音频文件URL，可选
            audio_file_path: 本地音频文件路径，可选
            **kwargs: 其他参数
            
        Returns:
            识别结果
        """
        if not audio_url and not audio_file_path:
            raise ValueError("必须提供audio_url或audio_file_path参数")
        
        try:
            # 优先使用URL
            audio_source = audio_url if audio_url else f"file://{audio_file_path}"
            
            # 构建请求消息
            messages = [
                {
                    "role": "user",
                    "content": [{"audio": audio_source}],
                }
            ]
            
            # 调用百炼API
            response = MultiModalConversation.call(
                model="qwen-audio-asr",
                messages=messages,
                result_format="message"
            )
            
            logger.info(f"语音识别原始结果: {response}")
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"语音识别失败: {response.message}")
                return {
                    "id": str(uuid.uuid4()),
                    "text": "",
                    "status": "error",
                    "error": response.message
                }
            
            # 解析响应结果
            content = response.output.choices[0].message.content
            
            # 确保返回的文本是字符串
            if isinstance(content, list):
                # 如果是列表，提取文本内容
                text = ""
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        text += item["text"]
                logger.info(f"从列表中提取的文本: {text}")
            elif isinstance(content, dict) and "text" in content:
                # 如果是字典且包含text字段
                text = content["text"]
                logger.info(f"从字典中提取的文本: {text}")
            elif isinstance(content, str):
                # 如果已经是字符串
                text = content
                logger.info(f"已经是字符串的文本: {text}")
            else:
                # 其他情况，尝试转换为字符串
                logger.warning(f"未知的响应格式: {type(content)}, 内容: {content}")
                text = str(content)
            
            return {
                "id": str(uuid.uuid4()),
                "text": text,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"语音识别出错: {str(e)}", exc_info=True)
            return {
                "id": str(uuid.uuid4()),
                "text": "",
                "status": "error",
                "error": str(e)
            }
    
    async def stream_recognize(self, 
                              audio_url: Optional[str] = None,
                              audio_file_path: Optional[str] = None,
                              **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式语音识别接口
        
        注意：当前实现是模拟流式响应，实际上是一次性获取结果后分块返回
        
        Args:
            audio_url: 音频文件URL，可选
            audio_file_path: 本地音频文件路径，可选
            **kwargs: 其他参数
            
        Yields:
            流式识别结果
        """
        if not audio_url and not audio_file_path:
            raise ValueError("必须提供audio_url或audio_file_path参数")
            
        try:
            # 获取完整识别结果
            result = await self.recognize(audio_url=audio_url, audio_file_path=audio_file_path, **kwargs)
            
            # 获取识别文本
            text = result.get("text", "")
            
            # 如果识别失败，直接返回错误
            if result.get("status") != "success" or not text:
                yield {
                    "id": result.get("id", str(uuid.uuid4())),
                    "text": "",
                    "status": "error",
                    "error": result.get("error", "识别失败")
                }
                return
            
            # 模拟流式响应，将文本分成多个部分返回
            # 这里简单地按句子或标点符号分割
            response_id = result.get("id", str(uuid.uuid4()))
            
            # 按标点符号分割文本
            segments = []
            current_segment = ""
            
            for char in text:
                current_segment += char
                # 遇到标点符号时分段
                if char in ["。", "，", "；", "！", "？", ".", ",", ";", "!", "?"]:
                    if current_segment.strip():
                        segments.append(current_segment)
                        current_segment = ""
            
            # 添加最后一段
            if current_segment.strip():
                segments.append(current_segment)
            
            # 如果没有分段，则整体作为一段
            if not segments:
                segments = [text]
            
            # 模拟流式返回
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
                
                # 添加一些延迟以模拟流式效果
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"流式语音识别出错: {str(e)}", exc_info=True)
            yield {
                "id": str(uuid.uuid4()),
                "text": "",
                "status": "error",
                "error": str(e)
            }


def register_dashscope_asr_service() -> Optional[DashScopeASRService]:
    """
    注册阿里云百炼语音识别服务
    
    Returns:
        DashScopeASRService实例，如果注册失败则返回None
    """
    try:
        # 从环境变量获取API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            logger.warning("未设置DASHSCOPE_API_KEY环境变量，无法注册阿里云百炼语音识别服务")
            return None
        
        # 创建并注册服务
        service = DashScopeASRService(api_key=api_key)
        AIServiceRegistry.register(service)
        
        logger.info(f"已注册阿里云百炼语音识别服务: {service.service_name}")
        return service
    except Exception as e:
        logger.error(f"注册阿里云百炼语音识别服务失败: {str(e)}", exc_info=True)
        return None
