"""
对象存储服务基类
定义了对象存储服务的通用接口
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Any, Optional, List, Union


class StorageServiceBase(ABC):
    """对象存储服务基类"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """服务名称"""
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> str:
        """服务类型"""
        pass
    
    @abstractmethod
    async def upload_file(self, file_path: str, object_key: str, **kwargs) -> str:
        """
        上传本地文件到对象存储
        
        Args:
            file_path: 本地文件路径
            object_key: 对象键名/路径
            **kwargs: 其他参数，如内容类型、访问控制等
            
        Returns:
            对象URL
        """
        pass
    
    @abstractmethod
    async def upload_data(self, data: Union[bytes, BinaryIO], object_key: str, **kwargs) -> str:
        """
        上传二进制数据到对象存储
        
        Args:
            data: 二进制数据或文件对象
            object_key: 对象键名/路径
            **kwargs: 其他参数，如内容类型、访问控制等
            
        Returns:
            对象URL
        """
        pass
    
    @abstractmethod
    async def download_file(self, object_key: str, file_path: str, **kwargs) -> str:
        """
        从对象存储下载文件到本地
        
        Args:
            object_key: 对象键名/路径
            file_path: 本地文件路径
            **kwargs: 其他参数
            
        Returns:
            本地文件路径
        """
        pass
    
    @abstractmethod
    async def download_data(self, object_key: str, **kwargs) -> bytes:
        """
        从对象存储下载对象数据
        
        Args:
            object_key: 对象键名/路径
            **kwargs: 其他参数
            
        Returns:
            对象数据
        """
        pass
    
    @abstractmethod
    async def delete_object(self, object_key: str, **kwargs) -> bool:
        """
        删除对象
        
        Args:
            object_key: 对象键名/路径
            **kwargs: 其他参数
            
        Returns:
            是否成功删除
        """
        pass
    
    @abstractmethod
    async def get_object_url(self, object_key: str, expires: int = 3600, **kwargs) -> str:
        """
        获取对象的URL
        
        Args:
            object_key: 对象键名/路径
            expires: URL过期时间（秒），默认为1小时
            **kwargs: 其他参数
            
        Returns:
            对象URL
        """
        pass
    
    @abstractmethod
    async def list_objects(self, prefix: str = "", **kwargs) -> List[Dict[str, Any]]:
        """
        列出对象
        
        Args:
            prefix: 对象前缀
            **kwargs: 其他参数
            
        Returns:
            对象列表
        """
        pass
