"""
数据库服务
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config import settings

# SQLite 配置：使用 StaticPool 避免连接池耗尽问题
# StaticPool 为整个进程维护单个连接，适合 SQLite 单文件数据库
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 需要
    poolclass=StaticPool,  # 使用静态连接池，避免连接泄漏
    echo=False  # 设置为 True 可以看到 SQL 日志
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
