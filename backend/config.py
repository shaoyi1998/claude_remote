"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Claude Remote"
    debug: bool = False

    # JWT 配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7天

    # 数据库配置
    database_url: str = "sqlite:///./claude_remote.db"

    # tmux 配置
    tmux_session_prefix: str = "claude_"

    # Claude Code 命令
    claude_command: str = "claude"

    class Config:
        env_file = ".env"


settings = Settings()
