"""
tmux 会话管理服务 (Linux/macOS 实现)
"""
import queue
import subprocess
import os
from typing import Optional

from .terminal_service import TerminalService, SHORTCUT_KEYS
from config import settings


class TmuxService(TerminalService):
    """tmux 会话管理"""

    def __init__(self):
        self.prefix = settings.tmux_session_prefix

    def _run_tmux(self, *args) -> tuple[bool, str]:
        """执行 tmux 命令"""
        try:
            result = subprocess.run(
                ["tmux"] + list(args),
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def session_exists(self, session_name: str) -> bool:
        """检查会话是否存在"""
        success, _ = self._run_tmux("has-session", "-t", session_name)
        return success

    def create_session(self, session_name: str, work_dir: str, command: str = None) -> bool:
        """创建新会话"""
        # 展开 ~ 为实际用户目录
        work_dir = os.path.expanduser(work_dir)

        # 确保工作目录存在
        os.makedirs(work_dir, exist_ok=True)

        # 创建会话
        success, output = self._run_tmux(
            "new-session",
            "-d",
            "-s", session_name,
            "-c", work_dir
        )

        if not success:
            return False

        # 启动命令
        cmd = command or settings.claude_command
        self._run_tmux("send-keys", "-t", session_name, cmd, "Enter")

        return True

    def kill_session(self, session_name: str) -> bool:
        """终止会话"""
        success, _ = self._run_tmux("kill-session", "-t", session_name)
        return success

    def send_command(self, session_name: str, command: str) -> bool:
        """向会话发送命令"""
        success, _ = self._run_tmux("send-keys", "-t", session_name, command, "Enter")
        return success

    def send_keys(self, session_name: str, keys: str) -> bool:
        """发送特殊按键(如 Ctrl+C, Escape 等)"""
        success, _ = self._run_tmux("send-keys", "-t", session_name, keys)
        return success

    def send_raw(self, session_name: str, data: str) -> bool:
        """发送原始输入（不自动添加回车，用于终端模拟器）"""
        # 使用 -l 选项发送字面字符，不解释特殊键
        success, _ = self._run_tmux("send-keys", "-t", session_name, "-l", data)
        return success

    def get_output(self, session_name: str, lines: int = 500) -> str:
        """获取会话输出（保留 ANSI 颜色代码）"""
        success, output = self._run_tmux(
            "capture-pane",
            "-t", session_name,
            "-p",
            "-e",  # 保留 ANSI 转义序列（颜色代码）
            "-S", f"-{lines}"
        )
        return output if success else ""

    def list_sessions(self) -> list[dict]:
        """列出所有 claude 相关会话"""
        success, output = self._run_tmux("list-sessions", "-F", "#{session_name}:#{session_attached}")
        if not success:
            return []

        sessions = []
        for line in output.strip().split("\n"):
            if line.startswith(self.prefix):
                parts = line.split(":")
                sessions.append({
                    "name": parts[0],
                    "attached": parts[1] == "1" if len(parts) > 1 else False
                })

        return sessions

    def resize_session(self, session_name: str, cols: int, rows: int) -> bool:
        """调整会话终端大小"""
        # tmux 使用 resize-window 命令
        # 注意：这需要会话存在
        if not self.session_exists(session_name):
            return False

        success, _ = self._run_tmux(
            "resize-window",
            "-t", session_name,
            "-x", str(cols),
            "-y", str(rows)
        )
        return success

    def get_output_queue(self, session_name: str) -> Optional[queue.Queue]:
        """tmux 不支持队列方式，返回 None 使用轮询"""
        return None
