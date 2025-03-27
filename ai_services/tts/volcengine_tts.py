"""
火山引擎语音合成服务实现
基于WebSocket的火山引擎TTS服务
"""
import os
import asyncio
import websockets
import uuid
import json
import gzip
import copy
import logging
from typing import Dict, Any, Optional, AsyncGenerator, BinaryIO, List

from ai_services.tts.base import TTSServiceBase

# 配置日志记录器
logger = logging.getLogger(__name__)

# 消息类型常量
MESSAGE_TYPES = {11: "audio-only server response", 12: "frontend server response", 15: "error message from server"}
MESSAGE_TYPE_SPECIFIC_FLAGS = {0: "no sequence number", 1: "sequence number > 0",
                               2: "last message from server (seq < 0)", 3: "sequence number < 0"}
MESSAGE_SERIALIZATION_METHODS = {0: "no serialization", 1: "JSON", 15: "custom type"}
MESSAGE_COMPRESSIONS = {0: "no compression", 1: "gzip", 15: "custom compression method"}

class VolcengineTTSService(TTSServiceBase):
    """火山引擎语音合成服务实现"""
    
    def __init__(self, appid: str, token: str, cluster: str, api_base: Optional[str] = None):
        """
        初始化火山引擎TTS服务
        
        Args:
            appid: 应用ID
            token: 访问令牌
            cluster: 集群名称
            api_base: API基础URL，默认为openspeech.bytedance.com
        """
        self.appid = appid
        self.token = token
        self.cluster = cluster
        self.host = api_base or "openspeech.bytedance.com"
        self.api_url = f"wss://{self.host}/api/v1/tts/ws_binary"
        
        # 默认请求头
        self.default_header = bytearray(b'\x11\x10\x11\x00')
        
        # 基础请求模板
        self.request_template = {
            "app": {
                "appid": self.appid,
                "token": self.token,  # 使用实际token
                "cluster": self.cluster
            },
            "user": {
                "uid": "user"  # 使用随机UUID替换
            },
            "audio": {
                "voice_type": "",  # 使用voice_id替换
                "encoding": "mp3",
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": "",  # 使用随机UUID替换
                "text": "",  # 使用实际文本替换
                "text_type": "plain",
                "operation": "submit"
            }
        }
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "volcengine"

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
        # 准备请求数据
        audio_data = bytearray()
        
        # 创建请求JSON
        request_json = self._create_request_json(text, voice_id, **kwargs)
        
        # 创建WebSocket请求
        full_request = self._create_ws_request(request_json)
        
        try:
            # 发送请求并接收响应
            header = {"Authorization": f"Bearer; {self.token}"}
            async with websockets.connect(self.api_url, additional_headers=header) as ws:
                await ws.send(full_request)
                
                # 接收并处理所有响应
                while True:
                    response = await ws.recv()
                    done, chunk = self._parse_response(response)
                    if chunk:
                        audio_data.extend(chunk)
                    if done:
                        break
        except Exception as e:
            logger.error(f"语音合成失败: {str(e)}", exc_info=True)
            raise
        
        return bytes(audio_data)
    
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
        # 创建请求JSON
        request_json = self._create_request_json(text, voice_id, **kwargs)
        
        # 创建WebSocket请求
        full_request = self._create_ws_request(request_json)
        
        try:
            # 发送请求并流式接收响应
            header = {"Authorization": f"Bearer; {self.token}"}
            async with websockets.connect(self.api_url, additional_headers=header) as ws:
                await ws.send(full_request)
                
                # 接收并处理所有响应
                while True:
                    response = await ws.recv()
                    done, chunk = self._parse_response(response)
                    if chunk:
                        yield bytes(chunk)
                    if done:
                        break
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
    
    def _create_request_json(self, text: str, voice_id: str, **kwargs) -> Dict[str, Any]:
        """
        创建请求JSON
        
        Args:
            text: 要合成的文本
            voice_id: 音色ID
            **kwargs: 其他参数
            
        Returns:
            请求JSON
        """
        # 复制请求模板
        request_json = copy.deepcopy(self.request_template)
        
        # 设置基本参数
        request_json["audio"]["voice_type"] = voice_id
        request_json["request"]["reqid"] = str(uuid.uuid4())
        request_json["request"]["text"] = text
        request_json["user"]["uid"] = str(uuid.uuid4())
        
        # 设置可选参数
        if "speed" in kwargs:
            request_json["audio"]["speed_ratio"] = float(kwargs["speed"])
        if "volume" in kwargs:
            request_json["audio"]["volume_ratio"] = float(kwargs["volume"])
        if "pitch" in kwargs:
            request_json["audio"]["pitch_ratio"] = float(kwargs["pitch"])
        if "encoding" in kwargs:
            request_json["audio"]["encoding"] = kwargs["encoding"]
        
        return request_json
    
    def _create_ws_request(self, request_json: Dict[str, Any]) -> bytearray:
        """
        创建WebSocket请求
        
        Args:
            request_json: 请求JSON
            
        Returns:
            WebSocket请求字节数组
        """
        # 序列化并压缩JSON
        payload_bytes = str.encode(json.dumps(request_json))
        payload_bytes = gzip.compress(payload_bytes)
        
        # 创建请求
        full_request = bytearray(self.default_header)
        full_request.extend((len(payload_bytes)).to_bytes(4, 'big'))  # payload size(4 bytes)
        full_request.extend(payload_bytes)  # payload
        
        return full_request
    
    def _parse_response(self, response: bytes) -> tuple[bool, bytearray]:
        """
        解析响应
        
        Args:
            response: 响应字节数组
            
        Returns:
            (是否完成, 音频数据块)
        """
        # 解析响应头
        protocol_version = response[0] >> 4
        header_size = response[0] & 0x0f
        message_type = response[1] >> 4
        message_type_specific_flags = response[1] & 0x0f
        serialization_method = response[2] >> 4
        message_compression = response[2] & 0x0f
        
        # 提取负载
        payload = response[header_size*4:]
        
        # 处理音频响应
        if message_type == 0xb:  # audio-only server response
            if message_type_specific_flags == 0:  # no sequence number as ACK
                return False, bytearray()
            else:
                sequence_number = int.from_bytes(payload[:4], "big", signed=True)
                payload_size = int.from_bytes(payload[4:8], "big", signed=False)
                audio_data = payload[8:]
                
                # 判断是否为最后一个响应
                is_done = sequence_number < 0
                
                return is_done, audio_data
        elif message_type == 0xf:  # error message
            code = int.from_bytes(payload[:4], "big", signed=False)
            msg_size = int.from_bytes(payload[4:8], "big", signed=False)
            error_msg = payload[8:]
            if message_compression == 1:
                error_msg = gzip.decompress(error_msg)
            error_msg = str(error_msg, "utf-8")
            
            # 记录错误
            logger.error(f"火山引擎TTS错误: 代码={code}, 消息={error_msg}")
            
            return True, bytearray()
        else:
            return False, bytearray()


def register_volcengine_tts_service() -> Optional[VolcengineTTSService]:
    """
    注册火山引擎TTS服务
    
    Returns:
        火山引擎TTS服务实例，如果缺少必要的环境变量则返回None
    """
    # 从环境变量获取配置
    appid = os.getenv("VOLCENGINE_TTS_APPID")
    token = os.getenv("VOLCENGINE_TTS_TOKEN")
    cluster = os.getenv("VOLCENGINE_TTS_CLUSTER")
    api_base = os.getenv("VOLCENGINE_TTS_API_BASE")
    
    # 检查必要的环境变量
    if not all([appid, token, cluster]):
        logger.warning("未能注册火山引擎TTS服务: 缺少必要的环境变量")
        return None
    
    # 创建并返回服务实例
    return VolcengineTTSService(
        appid=appid,
        token=token,
        cluster=cluster,
        api_base=api_base
    )
