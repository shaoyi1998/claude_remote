"""
应用配置
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "Claude Remote"
    debug: bool = False

    # JWT 配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7天

    # 登录安全配置
    login_max_attempts: int = 5  # 最大登录尝试次数
    login_lockout_minutes: int = 1440  # 锁定时间（分钟），默认24小时

    # 数据库配置
    database_url: str = "sqlite:///./claude_remote.db"

    # tmux 配置
    tmux_session_prefix: str = "claude_"

    # Claude Code 命令
    claude_command: str = "claude"

    # CORS 配置（生产环境应设置具体域名，用逗号分隔）
    cors_origins: str = "*"  # 默认允许所有，生产环境应设置为具体域名

    class Config:
        env_file = ".env"

    def get_cors_origins(self) -> List[str]:
        """获取 CORS 允许的来源列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
