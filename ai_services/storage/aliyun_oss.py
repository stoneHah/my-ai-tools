"""
阿里云对象存储服务实现
基于oss2的阿里云OSS服务
"""
import os
import logging
from typing import BinaryIO, Dict, Any, Optional, List, Union

import oss2
from oss2.exceptions import OssError

from ai_services.storage.base import StorageServiceBase

# 配置日志记录器
logger = logging.getLogger(__name__)


class AliyunOSSService(StorageServiceBase):
    """阿里云对象存储服务实现"""
    
    def __init__(self, access_key_id: str, access_key_secret: str, endpoint: str, bucket_name: str):
        """
        初始化阿里云OSS服务
        
        Args:
            access_key_id: 访问密钥ID
            access_key_secret: 访问密钥密码
            endpoint: OSS终端节点
            bucket_name: 存储桶名称
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        
        # 创建认证对象
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        
        # 创建存储桶对象
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
    
    @property
    def service_name(self) -> str:
        """服务名称"""
        return "aliyun"

    @property
    def service_type(self) -> str:
        """服务类型"""
        return "storage"
    
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
        try:
            # 处理可选参数
            headers = {}
            if "content_type" in kwargs:
                headers["Content-Type"] = kwargs["content_type"]
            
            # 上传文件
            result = self.bucket.put_object_from_file(object_key, file_path, headers=headers)
            
            # 返回对象URL
            return self.bucket.sign_url('GET', object_key, 30*60)  # 30分钟URL
        except OssError as e:
            logger.error(f"上传文件到阿里云OSS失败: {str(e)}", exc_info=True)
            raise
    
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
        try:
            # 处理可选参数
            headers = {}
            if "content_type" in kwargs:
                headers["Content-Type"] = kwargs["content_type"]
            
            # 上传数据
            if isinstance(data, bytes):
                result = self.bucket.put_object(object_key, data, headers=headers)
            else:
                result = self.bucket.put_object(object_key, data, headers=headers)
            
            # 返回对象URL
            return self.bucket.sign_url('GET', object_key, 30*60)  # 30分钟URL
        except OssError as e:
            logger.error(f"上传数据到阿里云OSS失败: {str(e)}", exc_info=True)
            raise
    
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
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 下载文件
            self.bucket.get_object_to_file(object_key, file_path)
            
            return file_path
        except OssError as e:
            logger.error(f"从阿里云OSS下载文件失败: {str(e)}", exc_info=True)
            raise
    
    async def download_data(self, object_key: str, **kwargs) -> bytes:
        """
        从对象存储下载对象数据
        
        Args:
            object_key: 对象键名/路径
            **kwargs: 其他参数
            
        Returns:
            对象数据
        """
        try:
            # 下载对象
            result = self.bucket.get_object(object_key)
            
            # 读取数据
            return result.read()
        except OssError as e:
            logger.error(f"从阿里云OSS下载数据失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_object(self, object_key: str, **kwargs) -> bool:
        """
        删除对象
        
        Args:
            object_key: 对象键名/路径
            **kwargs: 其他参数
            
        Returns:
            是否成功删除
        """
        try:
            # 删除对象
            self.bucket.delete_object(object_key)
            
            return True
        except OssError as e:
            logger.error(f"删除阿里云OSS对象失败: {str(e)}", exc_info=True)
            return False
    
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
        try:
            # 生成签名URL
            url = self.bucket.sign_url('GET', object_key, expires)
            
            return url
        except OssError as e:
            logger.error(f"获取阿里云OSS对象URL失败: {str(e)}", exc_info=True)
            raise
    
    async def list_objects(self, prefix: str = "", **kwargs) -> List[Dict[str, Any]]:
        """
        列出对象
        
        Args:
            prefix: 对象前缀
            **kwargs: 其他参数
            
        Returns:
            对象列表
        """
        try:
            # 列出对象
            result = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                result.append({
                    "key": obj.key,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                    "type": obj.type,
                    "storage_class": obj.storage_class
                })
            
            return result
        except OssError as e:
            logger.error(f"列出阿里云OSS对象失败: {str(e)}", exc_info=True)
            raise


def register_aliyun_oss_service() -> Optional[AliyunOSSService]:
    """
    注册阿里云OSS服务
    
    Returns:
        阿里云OSS服务实例，如果缺少必要的环境变量则返回None
    """
    # 从环境变量获取配置
    access_key_id = os.getenv("ALIYUN_OSS_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET")
    endpoint = os.getenv("ALIYUN_OSS_ENDPOINT")
    bucket_name = os.getenv("ALIYUN_OSS_BUCKET_NAME")
    
    # 检查必要的环境变量
    if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
        logger.warning("未能注册阿里云OSS服务: 缺少必要的环境变量")
        return None
    
    # 创建并返回服务实例
    return AliyunOSSService(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint=endpoint,
        bucket_name=bucket_name
    )
