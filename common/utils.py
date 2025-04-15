"""
通用工具函数
"""
import time
import logging
import asyncio
from typing import Any, Dict, List, Union

from common.exceptions import BusinessException

logger = logging.getLogger(__name__)

def normalize_timestamp(timestamp: Union[float, int, None]) -> Union[int, None]:
    """
    将时间戳标准化为整数格式
    
    Args:
        timestamp: 输入的时间戳，可以是浮点数或整数
        
    Returns:
        标准化后的整数时间戳，如果输入为None则返回None
    """
    if timestamp is None:
        return None
    return int(timestamp)


def normalize_response(data: Any) -> Any:
    """
    标准化响应数据，处理时间戳等特殊字段
    
    Args:
        data: 输入的响应数据
        
    Returns:
        标准化后的响应数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # 处理时间戳字段
            if key.endswith('_at') and isinstance(value, (int, float)):
                result[key] = normalize_timestamp(value)
            else:
                result[key] = normalize_response(value)
        return result
    elif isinstance(data, list):
        return [normalize_response(item) for item in data]
    else:
        return data


async def download_file_content(url: str, timeout: int = 60) -> bytes:
    """
    下载文件内容
    
    Args:
        url: 文件URL
        timeout: 超时时间（秒）
        
    Returns:
        文件二进制数据
    """
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    raise BusinessException(
                        message=f"下载文件失败: HTTP状态码 {response.status}",
                        data={"url": url}
                    )
                return await response.read()
    except aiohttp.ClientError as e:
        logger.error(f"下载文件失败: {str(e)}", exc_info=True)
        raise BusinessException(
            message=f"下载文件失败: {str(e)}",
            data={"url": url}
        )
    except asyncio.TimeoutError:
        logger.error(f"下载文件超时: {url}", exc_info=True)
        raise BusinessException(
            message=f"下载文件超时，请稍后重试",
            data={"url": url}
        )


def get_audio_duration(file_path: str) -> float:
    """
    获取音频文件的时长（秒）
    
    Args:
        file_path: 音频文件路径
        
    Returns:
        音频时长（秒）
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(file_path)
        duration_seconds = len(audio) / 1000.0  # pydub以毫秒为单位
        return duration_seconds
    except Exception as e:
        logger.error(f"获取音频时长失败: {str(e)}", exc_info=True)
        raise BusinessException(
            message=f"获取音频时长失败: {str(e)}",
            data={"file_path": file_path}
        )


async def get_audio_duration_async(file_path: str) -> float:
    """
    异步获取音频文件的时长（秒）
    
    Args:
        file_path: 音频文件路径
        
    Returns:
        音频时长（秒）
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_audio_duration, file_path)


def get_audio_duration_from_bytes(audio_data: bytes, format: str = "mp3") -> float:
    """
    从二进制音频数据获取时长（秒）
    
    Args:
        audio_data: 音频二进制数据
        format: 音频格式，如mp3、wav等
        
    Returns:
        音频时长（秒）
    """
    import tempfile
    import os
    
    temp_file_path = None
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(audio_data)
        
        # 获取音频时长
        return get_audio_duration(temp_file_path)
    except Exception as e:
        logger.error(f"获取音频时长失败: {str(e)}", exc_info=True)
        return 0.0
    finally:
        # 删除临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {str(e)}")


async def get_audio_duration_from_bytes_async(audio_data: bytes, format: str = "mp3") -> float:
    """
    异步从二进制音频数据获取时长（秒）
    
    Args:
        audio_data: 音频二进制数据
        format: 音频格式，如mp3、wav等
        
    Returns:
        音频时长（秒）
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_audio_duration_from_bytes, audio_data, format)
