from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取测试配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

from dashscope.audio.tts_v2 import VoiceEnrollmentService

# sample_url = "http://yixuanhui.oss-cn-shanghai.aliyuncs.com/clone/10s%2B.WAV"
sample_url = "https://ai-tools66.oss-cn-beijing.aliyuncs.com/uploads/image/1744099834667.wav?Expires=1744103505&OSSAccessKeyId=LTAI5tKmXCiYAFEZsNvDTMCp&Signature=PkDl%2B0U0i%2FpBSI8oOzFeCczdLOU%3D"

voice_service = VoiceEnrollmentService(api_key=DASHSCOPE_API_KEY)
voice_id = voice_service.create_voice(target_model="cosyvoice-clone-v1",prefix="aihuitu", url=sample_url)
print(voice_id)