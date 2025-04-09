"""
基础数据访问对象
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

# 定义泛型类型变量
T = TypeVar('T')

class BaseDAO(Generic[T]):
    """
    基础数据访问对象，提供通用的CRUD操作
    
    泛型参数:
        T: 数据模型类型
    """
    
    @classmethod
    def get_by_id(cls, db: Session, model: Type[T], id_field: str, id_value: Any) -> Optional[T]:
        """
        根据ID获取记录
        
        Args:
            db: 数据库会话
            model: 数据模型类
            id_field: ID字段名
            id_value: ID值
            
        Returns:
            记录，如果不存在则返回None
        """
        # 刷新会话，确保获取最新数据
        db.flush()
        
        # 构建查询并执行
        return db.query(model).filter(getattr(model, id_field) == id_value).first()
    
    @classmethod
    def list_records(
        cls, 
        db: Session, 
        model: Type[T], 
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = None,
        desc_order: bool = False
    ) -> List[T]:
        """
        列出记录
        
        Args:
            db: 数据库会话
            model: 数据模型类
            filters: 过滤条件，字段名到值的映射
            skip: 跳过记录数
            limit: 返回记录数限制
            order_by: 排序字段
            desc_order: 是否降序排序
            
        Returns:
            记录列表
        """
        # 刷新会话，确保获取最新数据
        db.flush()
        
        # 构建查询
        query = db.query(model)
        
        # 添加过滤条件
        if filters:
            for field, value in filters.items():
                if value is not None:
                    query = query.filter(getattr(model, field) == value)
        
        # 添加排序
        if order_by:
            order_func = desc if desc_order else asc
            query = query.order_by(order_func(getattr(model, order_by)))
        
        # 分页
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    @classmethod
    def create(cls, db: Session, model: Type[T], data: Dict[str, Any]) -> T:
        """
        创建记录
        
        Args:
            db: 数据库会话
            model: 数据模型类
            data: 记录数据
            
        Returns:
            创建的记录
        """
        instance = model(**data)
        db.add(instance)
        db.flush()  # 只刷新，不提交
        return instance
    
    @classmethod
    def update(cls, db: Session, instance: T, data: Dict[str, Any]) -> T:
        """
        更新记录
        
        Args:
            db: 数据库会话
            instance: 记录实例
            data: 更新数据
            
        Returns:
            更新后的记录
        """
        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)
        
        db.flush()  # 只刷新，不提交
        return instance
    
    @classmethod
    def delete(cls, db: Session, instance: T) -> bool:
        """
        删除记录
        
        Args:
            db: 数据库会话
            instance: 记录实例
            
        Returns:
            是否删除成功
        """
        db.delete(instance)
        db.flush()  # 只刷新，不提交
        return True
