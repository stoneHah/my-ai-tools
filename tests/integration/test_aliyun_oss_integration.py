"""
阿里云对象存储服务集成测试
使用实际的阿里云OSS环境进行测试
"""
import os
import uuid
import asyncio
import tempfile
from pathlib import Path
import urllib.parse
import re

import pytest
from dotenv import load_dotenv

from ai_services.storage.aliyun_oss import AliyunOSSService

# 加载环境变量
load_dotenv()

# 获取测试配置
ACCESS_KEY_ID = os.getenv("ALIYUN_OSS_ACCESS_KEY_ID")
ACCESS_KEY_SECRET = os.getenv("ALIYUN_OSS_ACCESS_KEY_SECRET")
ENDPOINT = os.getenv("ALIYUN_OSS_ENDPOINT")
BUCKET_NAME = os.getenv("ALIYUN_OSS_BUCKET_NAME")

# 跳过测试的条件
SKIP_INTEGRATION_TESTS = not all([ACCESS_KEY_ID, ACCESS_KEY_SECRET, ENDPOINT, BUCKET_NAME])
skip_reason = "缺少阿里云OSS配置，跳过集成测试"

# 音频文件路径
AUDIO_FILE_PATH = "f:/code/python/my-ai-tools/temp/03cec8d4-a5dd-4905-803d-9c3048b3ee52.mp3"


def check_object_key_in_url(url, object_key):
    """检查对象键是否在URL中，考虑URL编码"""
    # 将斜杠替换为%2F
    encoded_key = object_key.replace("/", "%2F")
    return encoded_key in url


@pytest.mark.skipif(SKIP_INTEGRATION_TESTS, reason=skip_reason)
class TestAliyunOSSIntegration:
    """阿里云OSS集成测试类"""
    
    @pytest.fixture(scope="class")
    def service(self):
        """创建OSS服务实例"""
        return AliyunOSSService(
            access_key_id=ACCESS_KEY_ID,
            access_key_secret=ACCESS_KEY_SECRET,
            endpoint=ENDPOINT,
            bucket_name=BUCKET_NAME
        )
    
    @pytest.fixture
    def test_file_path(self):
        """创建测试文件"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp:
            temp.write(b"This is a test file for AliyunOSS integration test.")
            return temp.name
    
    @pytest.fixture
    def test_object_key(self):
        """生成测试对象键"""
        return f"test/integration/{uuid.uuid4()}.txt"
    
    @pytest.fixture
    def test_audio_object_key(self):
        """生成测试音频对象键"""
        return f"test/integration/audio/{uuid.uuid4()}.mp3"
    
    @pytest.mark.asyncio
    async def test_upload_and_download_file(self, service, test_file_path, test_object_key):
        """测试上传和下载文件"""
        try:
            # 上传文件
            url = await service.upload_file(test_file_path, test_object_key)
            assert url is not None
            assert BUCKET_NAME in url
            # 检查URL中是否包含对象键（考虑URL编码）
            assert check_object_key_in_url(url, test_object_key)
            
            # 下载文件
            download_path = os.path.join(tempfile.gettempdir(), f"download_{uuid.uuid4()}.txt")
            result = await service.download_file(test_object_key, download_path)
            assert result == download_path
            assert os.path.exists(download_path)
            
            # 验证文件内容
            with open(download_path, "rb") as f:
                content = f.read()
            with open(test_file_path, "rb") as f:
                original_content = f.read()
            assert content == original_content
            
            # 清理
            os.unlink(download_path)
        finally:
            # 删除测试对象
            await service.delete_object(test_object_key)
    
    @pytest.mark.asyncio
    async def test_upload_and_download_data(self, service, test_object_key):
        """测试上传和下载数据"""
        test_data = b"This is test data for AliyunOSS integration test."

        
        try:
            # 上传数据
            url = await service.upload_data(test_data, test_object_key)
            assert url is not None
            assert BUCKET_NAME in url
            # 检查URL中是否包含对象键（考虑URL编码）
            assert check_object_key_in_url(url, test_object_key)
            
            # 下载数据
            downloaded_data = await service.download_data(test_object_key)
            assert downloaded_data == test_data
        finally:
            # 删除测试对象
            await service.delete_object(test_object_key)
    
    @pytest.mark.asyncio
    async def test_upload_and_download_audio_file(self, service, test_audio_object_key):
        """测试上传和下载音频文件"""
        # 检查音频文件是否存在
        if not os.path.exists(AUDIO_FILE_PATH):
            pytest.skip(f"音频文件不存在: {AUDIO_FILE_PATH}")
        
        try:
            # 上传音频文件
            url = await service.upload_file(
                AUDIO_FILE_PATH, 
                test_audio_object_key,
                content_type="audio/mpeg"
            )
            assert url is not None
            print("上传音频文件URL:", url)
            print("测试音频对象键:", test_audio_object_key)
            print("URL编码后的对象键:", test_audio_object_key.replace("/", "%2F"))
            
            # 检查URL中是否包含对象键（考虑URL编码）
            assert check_object_key_in_url(url, test_audio_object_key)
            
            # 下载音频文件
            download_path = os.path.join(tempfile.gettempdir(), f"download_{uuid.uuid4()}.mp3")
            result = await service.download_file(test_audio_object_key, download_path)
            assert result == download_path
            assert os.path.exists(download_path)
            
            # 验证文件大小
            original_size = os.path.getsize(AUDIO_FILE_PATH)
            downloaded_size = os.path.getsize(download_path)
            assert downloaded_size == original_size
            
            # 清理
            os.unlink(download_path)
            
            # 测试获取音频文件URL
            audio_url = await service.get_object_url(test_audio_object_key, 3600)
            assert audio_url is not None
            assert BUCKET_NAME in audio_url
            # 检查URL中是否包含对象键（考虑URL编码）
            assert check_object_key_in_url(audio_url, test_audio_object_key)
            assert "Expires=" in audio_url or "expires=" in audio_url
            
        finally:
            # 删除测试对象
            await service.delete_object(test_audio_object_key)
    
    @pytest.mark.asyncio
    async def test_get_object_url(self, service, test_file_path, test_object_key):
        """测试获取对象URL"""
        try:
            # 上传文件
            await service.upload_file(test_file_path, test_object_key)
            
            # 获取URL
            url = await service.get_object_url(test_object_key, 3600)
            assert url is not None
            assert BUCKET_NAME in url
            # 检查URL中是否包含对象键（考虑URL编码）
            assert check_object_key_in_url(url, test_object_key)
            assert "Expires=" in url or "expires=" in url
        finally:
            # 删除测试对象
            await service.delete_object(test_object_key)
    
    @pytest.mark.asyncio
    async def test_list_objects(self, service, test_file_path):
        """测试列出对象"""
        prefix = f"test/integration/list_{uuid.uuid4()}"
        test_keys = [f"{prefix}/file{i}.txt" for i in range(3)]
        
        try:
            # 上传多个文件
            for key in test_keys:
                await service.upload_file(test_file_path, key)
            
            # 列出对象
            objects = await service.list_objects(prefix)
            assert len(objects) == 3
            
            # 验证对象键
            object_keys = [obj["key"] for obj in objects]
            for key in test_keys:
                assert key in object_keys
        finally:
            # 删除测试对象
            for key in test_keys:
                await service.delete_object(key)
    
    @pytest.mark.asyncio
    async def test_delete_object(self, service, test_file_path, test_object_key):
        """测试删除对象"""
        # 上传文件
        await service.upload_file(test_file_path, test_object_key)
        
        # 删除对象
        result = await service.delete_object(test_object_key)
        assert result is True
        
        # 验证对象已删除
        objects = await service.list_objects(os.path.dirname(test_object_key))
        object_keys = [obj["key"] for obj in objects]
        assert test_object_key not in object_keys


if __name__ == "__main__":
    if SKIP_INTEGRATION_TESTS:
        print(skip_reason)
    else:
        pytest.main(["-xvs", __file__])
