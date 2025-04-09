"""
任务数据模型定义
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship

from db.models.base import Base


class Task(Base):
    """任务基础模型"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False, comment="任务唯一标识")
    service_type = Column(String(32), nullable=False, comment="服务类型，如image、tts等")
    service_name = Column(String(32), nullable=False, comment="服务名称，如coze、volcengine等")
    status = Column(Enum("pending", "running", "completed", "failed", "error"), 
                   default="pending", nullable=False, comment="任务状态")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    parameters = Column(JSON, nullable=True, comment="任务参数")
    result = Column(JSON, nullable=True, comment="任务结果")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 任务特有字段，使用JSON存储不同类型任务的特有属性
    task_specific_data = Column(JSON, nullable=True, comment="任务特有数据，不同类型任务存储不同的属性")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "service_type": self.service_type,
            "service_name": self.service_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "parameters": self.parameters,
            "result": self.result,
            "error_message": self.error_message,
            "task_specific_data": self.task_specific_data
        }
