"""
Claude Remote - 后端入口
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import queue

from api import auth, tasks, users, files
from services.database import create_tables, SessionLocal
from services.terminal_service import SHORTCUT_KEYS
from models.task import Task
from models.user import User
from services.auth import verify_token
from platform_utils import get_terminal_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket 连接管理
active_websockets = {}


app = FastAPI(
    title="Claude Remote",
    description="Claude Code 远程任务管理中心 API",
    version="1.0.0"
)

# 启动时创建数据库表
create_tables()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(files.router, prefix="/api/files", tags=["文件"])


@app.get("/")
async def root():
    return {"message": "Claude Remote API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/platform")
async def get_platform():
    """获取当前平台信息"""
    from platform_utils import is_linux, is_wsl
    return {
        "linux": is_linux(),
        "wsl": is_wsl()
    }


@app.websocket("/ws/tasks/{task_id}")
async def websocket_terminal(websocket: WebSocket, task_id: str):
    """WebSocket 终端连接"""
    await websocket.accept()

    # 从 query 参数获取 token
    token = websocket.query_params.get("token")

    # 验证 token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user = verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="Invalid token")
        return

    db = SessionLocal()
    session_name = None
    try:
        task = db.query(Task).filter(Task.id == int(task_id)).first()
        if not task:
            logger.warning(f"Task {task_id} not found")
            await websocket.close()
            return

        session_name = task.tmux_session
        terminal = get_terminal_service()

        # 检查会话是否存在
        if not terminal.session_exists(session_name):
            logger.warning(f"Session {session_name} not found for task {task_id}")
            await websocket.send_json({"type": "output", "data": "会话已结束，请恢复任务或创建新任务"})
            await websocket.close()
            return

        # 注册连接
        if session_name not in active_websockets:
            active_websockets[session_name] = set()
        active_websockets[session_name].add(websocket)

        logger.info(f"WebSocket connected for task {task_id}, session {session_name}")

        # 获取输出队列（线程安全队列）
        output_queue = terminal.get_output_queue(session_name)

        # 发送初始输出
        output = terminal.get_output(session_name)
        last_output = output
        if output:
            logger.info(f"Sending initial output: {len(output)} bytes")
            await websocket.send_json({"type": "output", "data": output})

        # 轮询计数器（用于定期获取完整输出比对）
        poll_count = 0

        # 处理消息循环
        while True:
            try:
                # 使用短超时等待 WebSocket 消息
                try:
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    data = json.loads(msg)

                    if data.get("type") == "input":
                        terminal.send_raw(session_name, data.get("data", ""))
                    elif data.get("type") == "resize":
                        cols = data.get("cols", 80)
                        rows = data.get("rows", 24)
                        terminal.resize_session(session_name, cols, rows)

                except asyncio.TimeoutError:
                    pass
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message")
                    pass

                # 从队列中获取新输出（非阻塞）
                if output_queue:
                    deltas = []
                    try:
                        while True:
                            delta = output_queue.get_nowait()
                            deltas.append(delta)
                    except queue.Empty:
                        pass  # 队列为空，正常情况

                    if deltas:
                        combined = ''.join(deltas)
                        logger.debug(f"Sending {len(combined)} bytes to WebSocket")
                        await websocket.send_json({
                            "type": "output",
                            "data": combined,
                            "append": True
                        })
                else:
                    # 没有队列时使用轮询方式（tmux）
                    poll_count += 1
                    if poll_count >= 3:  # 每 3 次循环轮询一次（约 300ms）
                        poll_count = 0
                        current_output = terminal.get_output(session_name)
                        if current_output != last_output:
                            # 输出有变化，发送完整更新
                            await websocket.send_json({
                                "type": "output",
                                "data": current_output,
                                "append": False
                            })
                            last_output = current_output

            except Exception as e:
                logger.info(f"WebSocket 连接结束: {type(e).__name__}: {e}")
                break

    finally:
        if session_name and session_name in active_websockets:
            active_websockets[session_name].discard(websocket)
        db.close()
