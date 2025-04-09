"""
全局数据库连接配置
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import logging


# 加载环境变量
load_dotenv()

# 数据库连接配置
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DB_NAME", "ai_tools")

print(f"数据库连接配置: {DB_HOST}:{DB_PORT}/{DB_NAME}:{DB_PASSWORD}")

# 数据库连接URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设置为True以显示SQL语句
    pool_recycle=3600,  # 连接回收时间
    pool_pre_ping=True  # 连接前ping一下，确保连接有效
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 初始化数据库
def init_db():
    """
    初始化数据库
    
    创建所有表并确保数据库结构是最新的
    """
    from db.models.base import Base
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logging.info("数据库初始化完成")
    except Exception as e:
        logging.error(f"数据库初始化失败: {str(e)}")
        raise
