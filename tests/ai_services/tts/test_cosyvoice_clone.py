"""
CosyVoice语音克隆服务单元测试
"""
import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

# 添加项目根目录到系统路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from ai_services.tts.cosyvoice_tts import CosyVoiceTTSService


class TestCosyVoiceClone(unittest.TestCase):
    """测试CosyVoice语音克隆服务"""
    
    def setUp(self):
        """测试前准备"""
        # 创建CosyVoice服务实例
        self.api_key = "test_api_key"
        self.service = CosyVoiceTTSService(api_key=self.api_key)
        
        # 测试数据
        self.sample_url = "https://example.com/audio_sample.mp3"
        self.voice_name = "test_voice"
        self.user_id = "test_user"
        self.app_id = "test_app"
        self.task_id = str(uuid.uuid4())
        
        # 模拟响应数据
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.output = {
            "task_id": self.task_id,
            "status": "pending",
            "message": "任务已提交",
            "created_at": "2025-04-01T15:00:00Z"
        }
    
    @patch('dashscope.audio.tts.VoiceClone.call')
    def test_create_clone_voice(self, mock_voice_clone_call):
        """测试创建克隆音色"""
        # 设置模拟返回值
        mock_voice_clone_call.return_value = self.mock_response
        
        # 执行异步测试
        result = asyncio.run(self._async_test_create_clone_voice())
        
        # 断言调用了正确的API
        mock_voice_clone_call.assert_called_once()
        call_args = mock_voice_clone_call.call_args[1]
        self.assertEqual(call_args["model"], "cosyvoice-clone-v1")
        self.assertEqual(call_args["audio_url"], self.sample_url)
        self.assertEqual(call_args["voice_name"], self.voice_name)
        self.assertIsNotNone(call_args["task_id"])
        
        # 断言返回了正确的结果
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["user_id"], self.user_id)
        self.assertEqual(result["app_id"], self.app_id)
        self.assertEqual(result["sample_url"], self.sample_url)
        self.assertEqual(result["voice_name"], self.voice_name)
    
    async def _async_test_create_clone_voice(self):
        """异步测试创建克隆音色"""
        return await self.service.create_clone_voice(
            sample_url=self.sample_url,
            voice_name=self.voice_name,
            user_id=self.user_id,
            app_id=self.app_id
        )
    
    @patch('dashscope.audio.tts.VoiceClone.call')
    def test_create_clone_voice_error(self, mock_voice_clone_call):
        """测试创建克隆音色失败情况"""
        # 设置模拟返回值为错误
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.message = "参数错误"
        mock_voice_clone_call.return_value = mock_response
        
        # 执行异步测试，应该抛出异常
        with self.assertRaises(Exception) as context:
            asyncio.run(self._async_test_create_clone_voice())
        
        # 断言异常信息正确
        self.assertIn("创建克隆音色失败", str(context.exception))
    
    @patch('dashscope.audio.tts.VoiceClone.query')
    def test_query_clone_task(self, mock_voice_clone_query):
        """测试查询克隆任务状态"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output = {
            "status": "success",
            "message": "任务完成",
            "voice_id": "generated_voice_id",
            "created_at": "2025-04-01T15:00:00Z",
            "updated_at": "2025-04-01T15:10:00Z"
        }
        mock_voice_clone_query.return_value = mock_response
        
        # 执行异步测试
        result = asyncio.run(self._async_test_query_clone_task())
        
        # 断言调用了正确的API
        mock_voice_clone_query.assert_called_once_with(task_id=self.task_id)
        
        # 断言返回了正确的结果
        self.assertEqual(result["task_id"], self.task_id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["voice_id"], "generated_voice_id")
    
    async def _async_test_query_clone_task(self):
        """异步测试查询克隆任务状态"""
        return await self.service.query_clone_task(task_id=self.task_id)


if __name__ == "__main__":
    unittest.main()
