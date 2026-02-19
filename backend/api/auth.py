"""
认证 API
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from services.database import get_db
from services.auth import (
    verify_password,
    create_access_token,
    get_current_active_user
)
from services.rate_limiter import login_rate_limiter
from config import settings
from models.user import User

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 获取客户端 IP
    client_ip = login_rate_limiter._get_client_ip(request)

    # 检查是否被锁定
    is_locked, remaining_minutes = login_rate_limiter.is_locked(client_ip)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试次数过多，IP 已锁定 {remaining_minutes} 分钟",
        )

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        # 记录失败
        fail_count, triggered = login_rate_limiter.record_failure(client_ip)
        if triggered:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录尝试次数过多，IP 已锁定 24 小时",
            )
        else:
            remaining = settings.login_max_attempts - fail_count
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"用户名或密码错误，剩余尝试次数: {remaining}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 登录成功，重置计数
    login_rate_limiter.reset(client_ip)

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user
