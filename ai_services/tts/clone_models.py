"""
语音克隆数据模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from db.config import Base

class TTSCloneVoice(Base):
    """用户克隆音色"""
    __tablename__ = 'tts_clone_voices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    voice_id = Column(String(100), nullable=False, unique=True, comment='克隆音色ID')
    name = Column(String(100), nullable=False, comment='克隆音色名称')
    description = Column(Text, nullable=True, comment='音色描述')
    user_id = Column(String(100), nullable=False, index=True, comment='用户ID')
    app_id = Column(String(100), nullable=False, index=True, comment='应用ID')
    platform_id = Column(Integer, ForeignKey('tts_platforms.id'), nullable=False, comment='平台ID')
    original_sample_url = Column(String(255), nullable=True, comment='原始样本URL')
    is_streaming = Column(Boolean, default=True, comment='是否支持流式接口')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    platform = relationship("TTSPlatform", back_populates="clone_voices")
    languages = relationship("TTSCloneVoiceLanguage", back_populates="clone_voice")
    
    def __repr__(self):
        return f"<TTSCloneVoice(name='{self.name}', voice_id='{self.voice_id}')>"

class TTSCloneVoiceLanguage(Base):
    """克隆音色支持的语言"""
    __tablename__ = 'tts_clone_voice_languages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    clone_voice_id = Column(Integer, ForeignKey('tts_clone_voices.id'), nullable=False, comment='克隆音色ID')
    language_id = Column(Integer, ForeignKey('tts_languages.id'), nullable=False, comment='语言ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    clone_voice = relationship("TTSCloneVoice", back_populates="languages")
    language = relationship("TTSLanguage")
    
    def __repr__(self):
        return f"<TTSCloneVoiceLanguage(clone_voice_id={self.clone_voice_id}, language_id={self.language_id})>"

class TTSCloneTask(Base):
    """语音克隆任务"""
    __tablename__ = 'tts_clone_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), nullable=False, unique=True, comment='任务ID')
    user_id = Column(String(100), nullable=False, index=True, comment='用户ID')
    app_id = Column(String(100), nullable=False, index=True, comment='应用ID')
    sample_url = Column(String(255), nullable=False, comment='样本URL')
    voice_name = Column(String(100), nullable=False, comment='音色名称')
    status = Column(String(20), nullable=False, default='pending', comment='任务状态')
    result_voice_id = Column(String(100), nullable=True, comment='结果音色ID')
    platform_id = Column(Integer, ForeignKey('tts_platforms.id'), nullable=False, comment='平台ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    platform = relationship("TTSPlatform")
    
    def __repr__(self):
        return f"<TTSCloneTask(task_id='{self.task_id}', status='{self.status}')>"
