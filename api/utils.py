"""
API工具函数模块
提供API模块共享的工具函数
"""
import logging
from typing import Optional

from db.service.task_service import TaskService
from db.config import get_db

# 全局任务服务实例
_task_service: Optional[TaskService] = None

def get_task_service() -> TaskService:
    """
    获取全局任务服务实例
    
    Returns:
        任务服务实例
    """
    global _task_service
    if _task_service is None:
        _task_service = TaskService(next(get_db()))
    return _task_service
