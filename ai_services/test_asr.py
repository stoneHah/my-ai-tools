"""
测试阿里云百炼语音识别服务
"""
import os
import asyncio
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from ai_services.dashscope_service import DashScopeASRService

async def test_asr_service():
    """测试语音识别服务"""
    # 获取API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误: 未设置DASHSCOPE_API_KEY环境变量")
        return
    
    # 创建服务实例
    asr_service = DashScopeASRService(api_key=api_key)
    
    # 测试音频URL
    audio_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"
    
    print(f"开始通过URL识别音频: {audio_url}")
    
    try:
        # 调用语音识别服务 - URL方式
        result = await asr_service.recognize(audio_url=audio_url)
        
        # 打印结果
        print("\nURL识别结果:")
        print(f"ID: {result.get('id', '')}")
        print(f"文本: {result.get('text', '')}")
        
        # 测试本地文件识别
        # 注意：这里需要一个实际存在的本地音频文件路径
        # 为了演示，我们可以下载示例音频到本地
        import requests
        local_file_path = "welcome.mp3"
        
        # 下载示例音频
        print(f"\n下载示例音频到本地: {local_file_path}")
        response = requests.get(audio_url)
        with open(local_file_path, "wb") as f:
            f.write(response.content)
        
        print(f"开始通过本地文件识别音频: {local_file_path}")
        
        # 调用语音识别服务 - 本地文件方式
        result_local = await asr_service.recognize(audio_file_path=local_file_path)
        
        # 打印结果
        print("\n本地文件识别结果:")
        print(f"ID: {result_local.get('id', '')}")
        print(f"文本: {result_local.get('text', '')}")
        
        # 测试流式API - URL方式
        print("\n测试URL流式识别:")
        async for chunk in asr_service.stream_recognize(audio_url=audio_url):
            print(f"收到流式数据: {json.dumps(chunk, ensure_ascii=False)}")
        
        # 测试流式API - 本地文件方式
        print("\n测试本地文件流式识别:")
        async for chunk in asr_service.stream_recognize(audio_file_path=local_file_path):
            print(f"收到流式数据: {json.dumps(chunk, ensure_ascii=False)}")
        
        # 清理临时文件
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            print(f"\n已清理临时文件: {local_file_path}")
        
    except Exception as e:
        print(f"识别出错: {str(e)}")
        # 确保清理临时文件
        if 'local_file_path' in locals() and os.path.exists(local_file_path):
            os.remove(local_file_path)

if __name__ == "__main__":
    asyncio.run(test_asr_service())
