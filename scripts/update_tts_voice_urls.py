"""
更新TTS音色头像和试听URL
"""
import os
import sys
# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_services.tts.models import TTSVoice
from db.config import DATABASE_URL

def update_voice_urls():
    # 创建数据库连接
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 读取Excel文件
        df = pd.read_excel('火山-豆包语音大模型音色列表_带头像.xlsx')
        
        # 获取所有TTS音色
        voices = session.query(TTSVoice).all()
        
        # 更新计数器
        updated_count = 0
        
        # 遍历所有音色
        for voice in voices:
            # 在Excel中查找匹配的行
            matching_row = df[df['清理后名称'] == voice.name]
            
            if not matching_row.empty:
                # 获取第一个匹配行
                row = matching_row.iloc[0]
                
                # 更新URL
                voice.avatar_url = row['火山头像url']
                voice.sample_audio_url = row['音色试听url']
                updated_count += 1
        
        # 提交更改
        session.commit()
        print(f"成功更新 {updated_count} 个音色的URL信息")

    except Exception as e:
        print(f"更新过程中出现错误: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == '__main__':
    update_voice_urls()
