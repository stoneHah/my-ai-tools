"""
数据库事务管理模块
"""
from contextlib import contextmanager
from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session):
    """
    事务上下文管理器
    
    使用示例:
    ```python
    with transaction(db):
        # 执行数据库操作
        # 如果没有异常，事务会在退出上下文时自动提交
        # 如果有异常，事务会自动回滚
    ```
    
    Args:
        db: 数据库会话
    """
    try:
        # 确保会话是干净的
        db.flush()
        
        # 执行上下文中的操作
        yield
        
        # 如果没有异常，提交事务
        db.commit()
    except:
        # 如果有异常，回滚事务
        db.rollback()
        raise
