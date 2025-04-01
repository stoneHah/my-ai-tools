"""
TTS音色数据模型定义
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, foreign

from db.config import Base

# 音色和语言的多对多关系表
voice_language_association = Table(
    'voice_language_association',
    Base.metadata,
    Column('voice_id', Integer, ForeignKey('tts_voices.id'), primary_key=True),
    Column('language_id', Integer, ForeignKey('tts_languages.id'), primary_key=True)
)

class TTSPlatform(Base):
    """语音合成平台"""
    __tablename__ = 'tts_platforms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='平台名称')
    code = Column(String(20), nullable=False, unique=True, comment='平台代码')
    description = Column(Text, nullable=True, comment='平台描述')
    api_base_url = Column(String(255), nullable=True, comment='API基础URL')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    voices = relationship("TTSVoice", back_populates="platform")
    clone_voices = relationship("TTSCloneVoice", back_populates="platform", primaryjoin="TTSPlatform.id == foreign(TTSCloneVoice.platform_id)")
    
    def __repr__(self):
        return f"<TTSPlatform(name='{self.name}', code='{self.code}')>"

class TTSVoiceCategory(Base):
    """音色分类"""
    __tablename__ = 'tts_voice_categories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='分类名称')
    description = Column(Text, nullable=True, comment='分类描述')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    voices = relationship("TTSVoice", back_populates="category")
    
    def __repr__(self):
        return f"<TTSVoiceCategory(name='{self.name}')>"

class TTSLanguage(Base):
    """支持的语言"""
    __tablename__ = 'tts_languages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='语言名称')
    code = Column(String(20), nullable=False, unique=True, comment='语言代码')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    voices = relationship("TTSVoice", secondary=voice_language_association, back_populates="languages")
    
    def __repr__(self):
        return f"<TTSLanguage(name='{self.name}', code='{self.code}')>"

class TTSVoice(Base):
    """TTS音色"""
    __tablename__ = 'tts_voices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    voice_id = Column(String(100), nullable=False, unique=True, comment='音色ID')
    name = Column(String(100), nullable=False, comment='音色名称')
    gender = Column(String(20), nullable=True, comment='性别')
    description = Column(Text, nullable=True, comment='音色描述')
    platform_id = Column(Integer, ForeignKey('tts_platforms.id'), nullable=False, comment='平台ID')
    category_id = Column(Integer, ForeignKey('tts_voice_categories.id'), nullable=True, comment='分类ID')
    is_streaming = Column(Boolean, default=True, comment='是否支持流式接口')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    platform = relationship("TTSPlatform", back_populates="voices")
    category = relationship("TTSVoiceCategory", back_populates="voices")
    languages = relationship("TTSLanguage", secondary=voice_language_association, back_populates="voices")
    
    def __repr__(self):
        return f"<TTSVoice(name='{self.name}', voice_id='{self.voice_id}')>"

# 导入克隆音色模型，避免循环导入
from ai_services.tts.clone_models import TTSCloneVoice
