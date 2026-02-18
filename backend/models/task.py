"""
任务模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from services.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 任务名称
    session_name = Column(String, nullable=True)  # Claude 会话名称(用于 --resume)
    tmux_session = Column(String, unique=True, nullable=False)  # tmux 会话名
    work_dir = Column(String, nullable=False)  # 工作目录
    status = Column(String, default="running")  # running, stopped, error

    # 启动参数
    skip_permissions = Column(Boolean, default=False)  # --dangerously-skip-permissions
    continue_session = Column(Boolean, default=False)  # --continue
    teammate_mode = Column(Boolean, default=False)  # --teammate-mode auto

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="tasks")


class QuickProject(Base):
    """快速启动项目配置"""
    __tablename__ = "quick_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # 项目名称
    path = Column(String, nullable=False)  # 项目路径
    skip_permissions = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联用户
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref="quick_projects")
