"""
阿里云对象存储服务单元测试
"""
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

import pytest
from oss2.exceptions import OssError

from ai_services.storage.aliyun_oss import AliyunOSSService


class TestAliyunOSSService(unittest.TestCase):
    """阿里云OSS服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.endpoint = "oss-cn-hangzhou.aliyuncs.com"
        self.bucket_name = "test-bucket"
        
        # 创建服务实例
        with patch('oss2.Auth'), patch('oss2.Bucket'):
            self.service = AliyunOSSService(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint=self.endpoint,
                bucket_name=self.bucket_name
            )
    
    @patch('oss2.Bucket.put_object_from_file')
    @patch('oss2.Bucket.sign_url')
    def test_upload_file(self, mock_sign_url, mock_put_object):
        """测试上传文件"""
        # 设置模拟返回值
        mock_sign_url.return_value = "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt"
        
        # 执行测试
        result = asyncio.run(self.service.upload_file("test.txt", "test.txt"))
        
        # 验证结果
        mock_put_object.assert_called_once()
        mock_sign_url.assert_called_once_with('GET', 'test.txt', 0)
        self.assertEqual(result, "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt")
    
    @patch('oss2.Bucket.put_object')
    @patch('oss2.Bucket.sign_url')
    def test_upload_data(self, mock_sign_url, mock_put_object):
        """测试上传数据"""
        # 设置模拟返回值
        mock_sign_url.return_value = "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt"
        
        # 执行测试
        data = b"test data"
        result = asyncio.run(self.service.upload_data(data, "test.txt"))
        
        # 验证结果
        mock_put_object.assert_called_once()
        mock_sign_url.assert_called_once_with('GET', 'test.txt', 0)
        self.assertEqual(result, "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt")
    
    @patch('oss2.Bucket.get_object_to_file')
    def test_download_file(self, mock_get_object):
        """测试下载文件"""
        # 执行测试
        with patch('os.makedirs') as mock_makedirs:
            result = asyncio.run(self.service.download_file("test.txt", "test.txt"))
        
        # 验证结果
        mock_makedirs.assert_called_once()
        mock_get_object.assert_called_once_with("test.txt", "test.txt")
        self.assertEqual(result, "test.txt")
    
    @patch('oss2.Bucket.get_object')
    def test_download_data(self, mock_get_object):
        """测试下载数据"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.read.return_value = b"test data"
        mock_get_object.return_value = mock_response
        
        # 执行测试
        result = asyncio.run(self.service.download_data("test.txt"))
        
        # 验证结果
        mock_get_object.assert_called_once_with("test.txt")
        self.assertEqual(result, b"test data")
    
    @patch('oss2.Bucket.delete_object')
    def test_delete_object(self, mock_delete_object):
        """测试删除对象"""
        # 执行测试
        result = asyncio.run(self.service.delete_object("test.txt"))
        
        # 验证结果
        mock_delete_object.assert_called_once_with("test.txt")
        self.assertTrue(result)
    
    @patch('oss2.Bucket.delete_object')
    def test_delete_object_error(self, mock_delete_object):
        """测试删除对象出错"""
        # 设置模拟异常
        mock_delete_object.side_effect = OssError("Test error", "test-request-id")
        
        # 执行测试
        result = asyncio.run(self.service.delete_object("test.txt"))
        
        # 验证结果
        mock_delete_object.assert_called_once_with("test.txt")
        self.assertFalse(result)
    
    @patch('oss2.Bucket.sign_url')
    def test_get_object_url(self, mock_sign_url):
        """测试获取对象URL"""
        # 设置模拟返回值
        mock_sign_url.return_value = "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt?Expires=3600"
        
        # 执行测试
        result = asyncio.run(self.service.get_object_url("test.txt", 3600))
        
        # 验证结果
        mock_sign_url.assert_called_once_with('GET', 'test.txt', 3600)
        self.assertEqual(result, "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt?Expires=3600")
    
    @patch('oss2.ObjectIterator')
    def test_list_objects(self, mock_object_iterator):
        """测试列出对象"""
        # 设置模拟返回值
        mock_obj1 = MagicMock()
        mock_obj1.key = "test1.txt"
        mock_obj1.size = 100
        mock_obj1.last_modified = 1234567890
        mock_obj1.etag = "etag1"
        mock_obj1.type = "Normal"
        mock_obj1.storage_class = "Standard"
        
        mock_obj2 = MagicMock()
        mock_obj2.key = "test2.txt"
        mock_obj2.size = 200
        mock_obj2.last_modified = 1234567891
        mock_obj2.etag = "etag2"
        mock_obj2.type = "Normal"
        mock_obj2.storage_class = "Standard"
        
        mock_object_iterator.return_value = [mock_obj1, mock_obj2]
        
        # 执行测试
        result = asyncio.run(self.service.list_objects("test"))
        
        # 验证结果
        mock_object_iterator.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["key"], "test1.txt")
        self.assertEqual(result[1]["key"], "test2.txt")
    
    @patch('oss2.ObjectIterator')
    def test_list_objects_error(self, mock_object_iterator):
        """测试列出对象出错"""
        # 设置模拟异常
        mock_object_iterator.side_effect = OssError("Test error", "test-request-id")
        
        # 执行测试并验证异常
        with self.assertRaises(OssError):
            asyncio.run(self.service.list_objects("test"))


@pytest.mark.asyncio
class TestAliyunOSSServiceAsync:
    """阿里云OSS服务异步测试类"""
    
    @pytest.fixture
    def service(self):
        """创建服务实例"""
        with patch('oss2.Auth'), patch('oss2.Bucket'):
            return AliyunOSSService(
                access_key_id="test_access_key_id",
                access_key_secret="test_access_key_secret",
                endpoint="oss-cn-hangzhou.aliyuncs.com",
                bucket_name="test-bucket"
            )
    
    @patch('oss2.Bucket.put_object_from_file')
    @patch('oss2.Bucket.sign_url')
    async def test_upload_file_async(self, mock_sign_url, mock_put_object, service):
        """测试异步上传文件"""
        # 设置模拟返回值
        mock_sign_url.return_value = "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt"
        
        # 执行测试
        result = await service.upload_file("test.txt", "test.txt")
        
        # 验证结果
        mock_put_object.assert_called_once()
        mock_sign_url.assert_called_once_with('GET', 'test.txt', 0)
        assert result == "https://test-bucket.oss-cn-hangzhou.aliyuncs.com/test.txt"


if __name__ == '__main__':
    unittest.main()
