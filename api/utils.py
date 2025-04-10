"""
API工具函数模块
提供API模块共享的工具函数
"""
import logging
from typing import Optional
from fastapi import Depends

from db.service.task_service import TaskService
from db.config import get_db

def get_task_service(db=Depends(get_db)) -> TaskService:
    """
    获取任务服务实例
    
    为每个请求创建一个新的TaskService实例，确保使用独立的数据库会话
    
    Args:
        db: 数据库会话，由FastAPI依赖注入
        
    Returns:
        任务服务实例
    """
    return TaskService(db)
