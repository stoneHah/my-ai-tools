"""
阿里云百炼AI服务实现
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

from ai_services.base import AIServiceRegistry
from ai_services.asr.base import ASRServiceBase

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志级别为INFO

# 服务类型
SERVICE_TYPE = "asr"
SERVICE_NAME_QWEN_AUDIO_ASR = "qwen-audio-asr"
SERVICE_NAME_PARFORMER_V2 = "paraformer-v2"




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
        return "qwen-audio-asr"
    
    @property
    def service_type(self) -> str:
        """服务类型"""
        return SERVICE_TYPE
    
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
            response = dashscope.MultiModalConversation.call(
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


class DashScopeParaformerASRService(ASRServiceBase):
    """
    基于DashScope的语音识别服务 (paraformer-v2模型)
    """
    
    def __init__(self):
        """
        初始化DashScope Paraformer语音识别服务
        """
        super().__init__()
        self.model = SERVICE_NAME_PARFORMER_V2
        self.description = "基于DashScope的语音识别服务 (paraformer-v2模型)"

    @property
    def service_type(self) -> str:
        return SERVICE_TYPE
    
    @property
    def service_name(self) -> str:
        return self.model
    
    async def recognize(self, 
                       audio_url: Optional[str] = None,
                       audio_file_path: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        语音识别
        
        Args:
            audio_url: 音频URL
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Returns:
            识别结果
        """
        if not audio_url:
            raise ValueError("paraformer-v2模型只支持通过URL进行识别")
        
        try:
            # 调用 paraformer-v2 API (异步调用)
            task_response = dashscope.audio.asr.Transcription.async_call(
                model=self.model,
                file_urls=[audio_url],
                **kwargs
            )
            
            # 等待任务完成
            task_id = task_response.output.task_id
            logger.info(f"语音识别任务已创建，任务ID: {task_id}")
            
            # 等待任务完成
            transcription_response = dashscope.audio.asr.Transcription.wait(task=task_id)
            
            if transcription_response.status_code == HTTPStatus.OK:
                for transcription in transcription_response.output['results']:
                    url = transcription['transcription_url']
                    result = json.loads(request.urlopen(url).read().decode('utf8'))
                    print(json.dumps(result, indent=4, ensure_ascii=False))
                print('transcription done!')
            else:
                print('Error: ', transcription_response.output.message)
        except Exception as e:
            logger.error(f"语音识别异常: {str(e)}", exc_info=True)
            return {
                "id": "",
                "text": "",
                "status": "error",
                "error": str(e)
            }
    
    async def stream_recognize(self, 
                              audio_url: Optional[str] = None,
                              audio_file_path: Optional[str] = None,
                              **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式语音识别 (注意: paraformer-v2不支持真正的流式识别，这里模拟流式输出)
        
        Args:
            audio_url: 音频URL
            audio_file_path: 音频文件路径
            **kwargs: 其他参数
            
        Yields:
            识别结果片段
        """
        try:
            # 首先执行完整识别
            result = await self.recognize(audio_url=audio_url, audio_file_path=audio_file_path, **kwargs)
            
            if result.get("status") == "error":
                yield {
                    "id": result.get("id", ""),
                    "text": "",
                    "delta": "",
                    "status": "error",
                    "error": result.get("error", "未知错误"),
                    "is_final": True
                }
                return
            
            # 获取完整文本
            full_text = result.get("text", "")
            
            # 获取原始结果中的分段信息
            raw_result = result.get("raw_result", {})
            segments = raw_result.get("segments", [])
            
            if segments:
                # 如果有分段信息，按分段输出
                accumulated_text = ""
                for i, segment in enumerate(segments):
                    segment_text = segment.get("text", "")
                    accumulated_text += segment_text
                    yield {
                        "id": result.get("id", ""),
                        "text": accumulated_text,
                        "delta": segment_text,
                        "status": "success",
                        "is_final": i == len(segments) - 1,
                        "segment": segment  # 包含时间戳等信息
                    }
                    # 模拟延迟
                    await asyncio.sleep(0.2)
            else:
                # 如果没有分段信息，将文本按句子分割
                sentences = full_text.replace("。", "。|").replace("！", "！|").replace("？", "？|").split("|")
                sentences = [s for s in sentences if s.strip()]
                
                # 逐句输出
                accumulated_text = ""
                for i, sentence in enumerate(sentences):
                    accumulated_text += sentence
                    yield {
                        "id": result.get("id", ""),
                        "text": accumulated_text,
                        "delta": sentence,
                        "status": "success",
                        "is_final": i == len(sentences) - 1
                    }
                    # 模拟延迟
                    await asyncio.sleep(0.2)
                
                # 如果没有句子，至少返回一个结果
                if not sentences:
                    yield {
                        "id": result.get("id", ""),
                        "text": full_text,
                        "delta": full_text,
                        "status": "success",
                        "is_final": True
                    }
        except Exception as e:
            logger.error(f"流式语音识别异常: {str(e)}", exc_info=True)
            yield {
                "id": "",
                "text": "",
                "delta": "",
                "status": "error",
                "error": str(e),
                "is_final": True
            }



def register_dashscope_asr_service() -> Optional[DashScopeASRService]:
    """
    注册阿里云百炼语音识别服务
    
    Returns:
        DashScopeASRService: 服务实例，如果注册失败则返回None
    """
    try:
        from ai_services.base import AIServiceRegistry
        
        # 创建服务实例
        service = DashScopeASRService()
        paraformer_service = DashScopeParaformerASRService()
        
        # 注册服
        AIServiceRegistry.register(service)
        AIServiceRegistry.register(paraformer_service)
        
        return service
    except Exception as e:
        logger.error(f"注册DashScope语音识别服务失败: {str(e)}", exc_info=True)
        return None
