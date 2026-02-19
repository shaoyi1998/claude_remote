"""
用户管理 API
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any

from services.database import get_db
from services.auth import get_password_hash, get_current_active_user
from models.user import User
from models.user_config import UserConfig

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class ConfigUpdate(BaseModel):
    shortcuts: Optional[Any] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建用户（需要已登录）"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(user)
    db.commit()

    return {"message": "用户创建成功"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改密码"""
    from services.auth import verify_password

    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "密码修改成功"}


@router.post("/init")
async def init_admin(db: Session = Depends(get_db)):
    """初始化管理员账号（仅首次使用）"""
    # 检查是否已有用户
    existing = db.query(User).first()
    if existing:
        raise HTTPException(status_code=400, detail="已存在用户，无法初始化")

    # 创建默认管理员（默认密码建议首次登录后修改）
    admin = User(
        username="admin",
        hashed_password=get_password_hash("admin123")
    )
    db.add(admin)
    db.commit()

    return {
        "message": "管理员账号创建成功",
        "username": "admin",
        "hint": "默认密码已设置，请登录后立即修改密码"
    }


@router.get("/config")
async def get_user_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户配置"""
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    if config and config.shortcuts_json:
        try:
            return {"shortcuts": json.loads(config.shortcuts_json)}
        except json.JSONDecodeError:
            return {"shortcuts": None}
    return {"shortcuts": None}


@router.post("/config")
async def save_user_config(
    data: ConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """保存用户配置"""
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    shortcuts_json = json.dumps(data.shortcuts) if data.shortcuts else None

    if config:
        config.shortcuts_json = shortcuts_json
    else:
        config = UserConfig(
            user_id=current_user.id,
            shortcuts_json=shortcuts_json
        )
        db.add(config)
    db.commit()
    return {"message": "配置已保存"}
