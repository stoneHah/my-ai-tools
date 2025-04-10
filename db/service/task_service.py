"""
任务服务层
"""
from typing import List, Optional, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session

from db.config import get_db
from db.dao.task_dao import TaskDAO
from db.models.task import Task
from db.transaction import transaction


class TaskService:
    """任务服务"""
    
    def __init__(self, db: Session = Depends(get_db)):
        """
        初始化任务服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def create_task(
        self,
        service_type: str,
        service_name: str,
        status: str = "pending",
        parameters: Optional[Dict[str, Any]] = None,
        task_specific_data: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        创建任务
        
        Args:
            service_type: 服务类型
            service_name: 服务名称
            status: 任务状态
            parameters: 任务参数
            task_specific_data: 任务特有数据
            
        Returns:
            创建的任务
        """
        task = None
        with transaction(self.db):
            task = TaskDAO.create_task(
                db=self.db,
                service_type=service_type,
                service_name=service_name,
                status=status,
                parameters=parameters,
                task_specific_data=task_specific_data
            )
        
        # 事务提交后刷新实例
        self.db.refresh(task)
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务，如果不存在则返回None
        """
        return TaskDAO.get_task_by_id(db=self.db, task_id=task_id)
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        task_specific_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            result: 任务结果
            error_message: 错误信息
            task_specific_data: 任务特有数据
            
        Returns:
            更新后的任务，如果任务不存在则返回None
        """
        task = None
        with transaction(self.db):
            task = TaskDAO.update_task_status(
                db=self.db,
                task_id=task_id,
                status=status,
                result=result,
                error_message=error_message,
                task_specific_data=task_specific_data
            )
        
        if task:
            self.db.refresh(task)
        return task
    
    def list_tasks(
        self,
        service_type: Optional[str] = None,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        列出任务
        
        Args:
            service_type: 服务类型过滤
            service_name: 服务名称过滤
            status: 状态过滤
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            任务列表
        """
        return TaskDAO.list_tasks(
            db=self.db,
            service_type=service_type,
            service_name=service_name,
            status=status,
            skip=skip,
            limit=limit
        )
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        result = False
        with transaction(self.db):
            result = TaskDAO.delete_task(db=self.db, task_id=task_id)
        return result
