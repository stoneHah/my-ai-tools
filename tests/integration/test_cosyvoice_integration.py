"""
CosyVoice语音克隆服务集成测试
实际调用阿里云API进行测试
"""
import os
import sys
import unittest
import asyncio
import uuid
import time
from dotenv import load_dotenv

# 添加项目根目录到系统路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ai_services.tts.cosyvoice_tts import CosyVoiceTTSService

# 加载环境变量
load_dotenv()

# 跳过测试的装饰器
skip_if_no_api_key = unittest.skipIf(
    os.environ.get("DASHSCOPE_API_KEY") is None,
    "需要设置DASHSCOPE_API_KEY环境变量才能运行此测试"
)

class TestCosyVoiceIntegration(unittest.TestCase):
    """CosyVoice语音克隆服务集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 获取API密钥
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            self.skipTest("需要设置DASHSCOPE_API_KEY环境变量才能运行此测试")
        
        # 创建CosyVoice服务实例
        self.service = CosyVoiceTTSService(api_key=self.api_key)
        
        # 测试数据
        self.sample_url = "http://yixuanhui.oss-cn-shanghai.aliyuncs.com/clone/10s%2B.WAV"  # 替换为实际的样本URL
        self.voice_name = f"test_voice_{uuid.uuid4().hex[:8]}"  # 生成唯一的音色名称
        self.user_id = "test_user"
        self.app_id = "test_app"
        
        # 保存任务ID
        self.task_id = None
    
    @skip_if_no_api_key
    def test_create_and_query_clone_voice(self):
        """测试创建克隆音色并查询任务状态（实际API调用）"""
        # 执行异步测试
        result = asyncio.run(self._async_test_create_clone_voice())
        
        # 验证结果
        self.assertIn("task_id", result)
        self.assertIn("status", result)
        self.assertEqual(result["user_id"], self.user_id)
        self.assertEqual(result["app_id"], self.app_id)
        
        # 保存任务ID用于后续查询
        self.task_id = result["task_id"]
        print(f"\n创建克隆音色任务ID: {self.task_id}")
        
        # 等待一段时间后查询任务状态
        time.sleep(5)  # 等待5秒
        
        # 查询任务状态
        query_result = asyncio.run(self._async_test_query_clone_task())
        
        # 验证查询结果
        self.assertEqual(query_result["task_id"], self.task_id)
        self.assertIn("status", query_result)
        print(f"任务状态: {query_result['status']}")
        
        # 注意：实际克隆任务可能需要较长时间才能完成
        # 此测试只验证API调用是否成功，不等待任务完成
    
    @skip_if_no_api_key
    def test_synthesize_with_clone_voice(self):
        """测试使用克隆音色合成语音（需要已有克隆音色）"""
        # 此测试需要已经有一个可用的克隆音色ID
        # 可以从环境变量中获取，或者使用之前测试创建的音色
        clone_voice_id = os.environ.get("TEST_CLONE_VOICE_ID")
        if not clone_voice_id:
            self.skipTest("需要设置TEST_CLONE_VOICE_ID环境变量才能运行此测试")
        
        # 执行异步测试
        text = "这是一段使用克隆音色合成的测试语音。"
        result = asyncio.run(self._async_test_synthesize(text, clone_voice_id))
        
        # 验证结果是否为有效的音频数据
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 1000)  # 确保音频数据不为空
        
        # 可选：保存音频到文件进行手动验证
        output_path = f"test_clone_voice_{uuid.uuid4().hex[:8]}.mp3"
        with open(output_path, "wb") as f:
            f.write(result)
        print(f"\n已保存测试音频到: {output_path}")
    
    async def _async_test_create_clone_voice(self):
        """异步测试创建克隆音色"""
        return await self.service.create_clone_voice(
            sample_url=self.sample_url,
            voice_name=self.voice_name,
            user_id=self.user_id,
            app_id=self.app_id
        )
    
    async def _async_test_query_clone_task(self):
        """异步测试查询克隆任务状态"""
        return await self.service.query_clone_task(task_id=self.task_id)
    
    async def _async_test_synthesize(self, text, voice_id):
        """异步测试使用克隆音色合成语音"""
        return await self.service.synthesize(text=text, voice_id=voice_id)


if __name__ == "__main__":
    unittest.main()