"""
任务管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
import os

from services.database import get_db
from services.auth import get_current_active_user
from services.terminal_service import SHORTCUT_KEYS, validate_tmux_key
from models.user import User
from models.task import Task
from platform_utils import get_terminal_service, is_root

router = APIRouter()


class TaskCreate(BaseModel):
    name: str
    work_dir: str
    skip_permissions: bool = False
    teammate_mode: bool = False


class TaskUpdate(BaseModel):
    skip_permissions: Optional[bool] = None
    teammate_mode: Optional[bool] = None


class RawInput(BaseModel):
    data: str


class TaskResponse(BaseModel):
    id: int
    name: str
    tmux_session: str
    work_dir: str
    status: str
    skip_permissions: bool
    teammate_mode: bool

    class Config:
        from_attributes = True


class TaskDetail(TaskResponse):
    output: str
    teammate_mode: bool = False


@router.get("", response_model=list[TaskResponse])
async def get_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取任务列表"""
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()

    # 更新实际状态
    terminal = get_terminal_service()
    for task in tasks:
        if not terminal.session_exists(task.tmux_session):
            if task.status == "running":
                task.status = "stopped"
    db.commit()

    return tasks


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """新建任务"""
    terminal = get_terminal_service()

    # 生成唯一会话名
    session_name = f"claude_{uuid.uuid4().hex[:8]}"

    # 构建 claude 命令
    parts = ["claude"]

    # 团队模式
    if task_data.teammate_mode:
        parts.append("--teammate-mode auto")

    # 跳过权限
    if task_data.skip_permissions:
        if is_root():
            parts[0] = "IS_SANDBOX=1 claude"
            parts.append("--dangerously-skip-permissions")
        else:
            parts.append("--dangerously-skip-permissions")

    claude_cmd = " ".join(parts)

    # 创建终端会话
    success = terminal.create_session(session_name, task_data.work_dir, claude_cmd)
    if not success:
        raise HTTPException(status_code=500, detail="创建终端会话失败")

    # 保存到数据库
    task = Task(
        name=task_data.name,
        tmux_session=session_name,
        work_dir=task_data.work_dir,
        skip_permissions=task_data.skip_permissions,
        teammate_mode=task_data.teammate_mode,
        user_id=current_user.id
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取任务详情"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取输出
    terminal = get_terminal_service()
    output = terminal.get_output(task.tmux_session) if terminal.session_exists(task.tmux_session) else "会话已结束"

    return TaskDetail(
        id=task.id,
        name=task.name,
        tmux_session=task.tmux_session,
        work_dir=task.work_dir,
        status=task.status,
        skip_permissions=task.skip_permissions,
        teammate_mode=task.teammate_mode,
        output=output
    )


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新任务设置"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 更新设置
    if task_data.skip_permissions is not None:
        task.skip_permissions = task_data.skip_permissions
    if task_data.teammate_mode is not None:
        task.teammate_mode = task_data.teammate_mode

    db.commit()
    db.refresh(task)

    return task


@router.post("/{task_id}/input")
async def send_input(
    task_id: int,
    input_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """向任务发送输入"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查会话是否存在，不存在则恢复
    terminal = get_terminal_service()
    if not terminal.session_exists(task.tmux_session):
        # 尝试恢复会话
        success = terminal.create_session(task.tmux_session, task.work_dir, "claude --continue")
        if not success:
            raise HTTPException(status_code=400, detail="会话已结束且无法恢复")
        task.status = "running"
        db.commit()

    command = input_data.get("command", "")
    if not command:
        raise HTTPException(status_code=400, detail="命令不能为空")

    success = terminal.send_command(task.tmux_session, command)
    if not success:
        raise HTTPException(status_code=500, detail="发送命令失败")

    return {"message": "命令已发送"}


@router.post("/{task_id}/restore")
async def restore_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """恢复已停止的任务"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    terminal = get_terminal_service()
    if terminal.session_exists(task.tmux_session):
        return {"message": "任务仍在运行"}

    # 构建恢复命令
    parts = ["claude", "--continue"]

    # 团队模式
    if task.teammate_mode:
        parts.append("--teammate-mode auto")

    # 跳过权限
    if task.skip_permissions:
        if is_root():
            parts[0] = "IS_SANDBOX=1 claude"
            parts.append("--dangerously-skip-permissions")
        else:
            parts.append("--dangerously-skip-permissions")

    claude_cmd = " ".join(parts)

    # 重新创建会话
    success = terminal.create_session(task.tmux_session, task.work_dir, claude_cmd)
    if not success:
        raise HTTPException(status_code=500, detail="恢复会话失败")

    task.status = "running"
    db.commit()

    return {"message": "任务已恢复"}


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """终止会话（保留数据库记录，可恢复）"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 终止会话
    terminal = get_terminal_service()
    terminal.kill_session(task.tmux_session)

    # 更新状态为已停止
    task.status = "stopped"
    db.commit()

    return {"message": "任务已终止"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    delete_files: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除任务（可选删除工作目录）"""
    import shutil

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 终止会话（如果还在运行）
    terminal = get_terminal_service()
    terminal.kill_session(task.tmux_session)

    work_dir = task.work_dir

    # 从数据库删除
    db.delete(task)
    db.commit()

    # 可选：删除工作目录
    if delete_files and work_dir:
        try:
            expanded_dir = os.path.expanduser(work_dir)
            if os.path.exists(expanded_dir):
                shutil.rmtree(expanded_dir)
        except Exception as e:
            print(f"删除目录失败: {e}")

    return {"message": "任务已删除"}


@router.post("/{task_id}/shortcut")
async def send_shortcut(
    task_id: int,
    shortcut_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发送快捷键

    支持两种模式:
    1. 预定义快捷键: { "key": "ctrl_c" } - 使用 SHORTCUT_KEYS 映射
    2. tmux 格式: { "key": "C-c", "isTmuxFormat": true } - 直接使用 tmux 格式
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    terminal = get_terminal_service()
    if not terminal.session_exists(task.tmux_session):
        raise HTTPException(status_code=400, detail="会话已结束")

    shortcut = shortcut_data.get("key", "")
    is_tmux_format = shortcut_data.get("isTmuxFormat", False)

    if is_tmux_format:
        # 新模式：直接使用 tmux 格式，验证后发送
        if not validate_tmux_key(shortcut):
            raise HTTPException(status_code=400, detail=f"无效的快捷键格式: {shortcut}")

        # 处理原始转义序列（如果需要）
        if shortcut.startswith("RAW:"):
            raw_data = shortcut[4:]
            success = terminal.send_raw(task.tmux_session, raw_data)
        else:
            success = terminal.send_keys(task.tmux_session, shortcut)
    else:
        # 旧模式：使用预定义映射
        if shortcut not in SHORTCUT_KEYS:
            raise HTTPException(status_code=400, detail="未知快捷键")

        keys = SHORTCUT_KEYS[shortcut]

        # 处理原始转义序列
        if keys.startswith("RAW:"):
            raw_data = keys[4:]  # 去掉 "RAW:" 前缀
            success = terminal.send_raw(task.tmux_session, raw_data)
        else:
            success = terminal.send_keys(task.tmux_session, keys)

    if not success:
        raise HTTPException(status_code=500, detail="发送快捷键失败")

    return {"message": f"已发送 {shortcut}"}


@router.post("/{task_id}/raw-input")
async def send_raw_input(
    task_id: int,
    input_data: RawInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发送原始输入（用于终端模拟器）"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    terminal = get_terminal_service()
    if not terminal.session_exists(task.tmux_session):
        raise HTTPException(status_code=400, detail="会话已结束")

    success = terminal.send_raw(task.tmux_session, input_data.data)
    if not success:
        raise HTTPException(status_code=500, detail="发送输入失败")

    return {"message": "输入已发送"}


@router.get("/shortcuts/list")
async def list_shortcuts():
    """获取可用快捷键列表"""
    return {
        "shortcuts": [
            {"id": k, "name": _get_shortcut_name(k)}
            for k in SHORTCUT_KEYS.keys()
        ]
    }


def _get_shortcut_name(key: str) -> str:
    """获取快捷键中文名"""
    names = {
        # 方向键
        "up": "上",
        "down": "下",
        "left": "左",
        "right": "右",
        # 常用操作
        "escape": "Esc",
        "home": "Home",
        "end": "End",
        "backspace": "Backspace",
        "enter": "Enter",
        "paste": "粘贴",
        # 组合键
        "ctrl_c": "Ctrl+C",
        "shift_up": "Shift+上",
        "shift_down": "Shift+下",
        "shift_tab": "Shift+Tab",
    }
    return names.get(key, key)
