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
