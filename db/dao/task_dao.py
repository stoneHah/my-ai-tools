"""
任务数据访问对象
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models.task import Task
from db.dao.base_dao import BaseDAO


class TaskDAO(BaseDAO[Task]):
    """任务数据访问对象"""
    
    @staticmethod
    def create_task(
        db: Session,
        service_type: str,
        service_name: str,
        status: str = "pending",
        parameters: Optional[Dict[str, Any]] = None,
        task_specific_data: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        创建任务记录
        
        Args:
            db: 数据库会话
            service_type: 服务类型
            service_name: 服务名称
            status: 任务状态
            parameters: 任务参数
            task_specific_data: 任务特有数据
            
        Returns:
            创建的任务记录
        """
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            service_type=service_type,
            service_name=service_name,
            status=status,
            parameters=parameters,
            task_specific_data=task_specific_data
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: str) -> Optional[Task]:
        """
        根据任务ID获取任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            任务记录，如果不存在则返回None
        """
        return TaskDAO.get_by_id(db, Task, "task_id", task_id)
    
    @staticmethod
    def update_task_status(
        db: Session,
        task_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        task_specific_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        更新任务状态
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            status: 新状态
            result: 任务结果
            error_message: 错误信息
            task_specific_data: 任务特有数据
            
        Returns:
            更新后的任务记录，如果任务不存在则返回None
        """
        task = TaskDAO.get_task_by_id(db, task_id)
        if not task:
            return None
        
        task.status = status
        
        if result is not None:
            task.result = result
        
        if error_message is not None:
            task.error_message = error_message
            
        if task_specific_data is not None:
            # 如果已有task_specific_data，则合并而不是替换
            if task.task_specific_data:
                task.task_specific_data.update(task_specific_data)
            else:
                task.task_specific_data = task_specific_data
        
        if status == "completed" or status == "failed" or status == "error":
            task.completed_at = datetime.now()
        
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def list_tasks(
        db: Session,
        service_type: Optional[str] = None,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        列出任务
        
        Args:
            db: 数据库会话
            service_type: 服务类型过滤
            service_name: 服务名称过滤
            status: 状态过滤
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            任务记录列表
        """
        query = db.query(Task)
        
        if service_type:
            query = query.filter(Task.service_type == service_type)
        
        if service_name:
            query = query.filter(Task.service_name == service_name)
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.order_by(desc(Task.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def delete_task(db: Session, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        task = TaskDAO.get_task_by_id(db, task_id)
        if not task:
            return False
        
        db.delete(task)
        db.commit()
        return True
