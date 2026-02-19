"""
用户配置模型
用于存储用户个性化设置（如快捷键配置）
"""
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from services.database import Base


class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    shortcuts_json = Column(Text, nullable=True)  # JSON 格式存储快捷键配置

    user = relationship("User")
