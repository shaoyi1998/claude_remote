"""
终端服务抽象接口
用于抽象不同平台的终端实现 (tmux)
"""
import queue
from abc import ABC, abstractmethod
from typing import Optional


class TerminalService(ABC):
    """终端服务抽象基类"""

    @abstractmethod
    def session_exists(self, session_name: str) -> bool:
        """检查会话是否存在"""
        pass

    @abstractmethod
    def create_session(self, session_name: str, work_dir: str, command: str = None) -> bool:
        """创建新会话"""
        pass

    @abstractmethod
    def get_output(self, session_name: str, lines: int = 500) -> str:
        """获取会话输出"""
        pass

    @abstractmethod
    def kill_session(self, session_name: str) -> bool:
        """终止会话"""
        pass

    @abstractmethod
    def send_command(self, session_name: str, command: str) -> bool:
        """向会话发送命令（自动添加回车）"""
        pass

    @abstractmethod
    def send_keys(self, session_name: str, keys: str) -> bool:
        """发送特殊按键(如 Ctrl+C, Escape 等)"""
        pass

    @abstractmethod
    def send_raw(self, session_name: str, data: str) -> bool:
        """发送原始输入（不自动添加回车）"""
        pass

    @abstractmethod
    def list_sessions(self) -> list[dict]:
        """列出所有相关会话"""
        pass

    @abstractmethod
    def resize_session(self, session_name: str, cols: int, rows: int) -> bool:
        """调整会话终端大小"""
        pass

    @abstractmethod
    def get_output_queue(self, session_name: str) -> Optional[queue.Queue]:
        """获取输出队列（用于 WebSocket 实时推送）

        Returns:
            queue.Queue: 输出队列（如果支持）
            None: 不支持队列方式，使用轮询（tmux）
        """
        pass


# 快捷键映射表
# 特殊值以 RAW: 开头表示发送原始转义序列
SHORTCUT_KEYS = {
    # 方向键
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",

    # 常用操作
    "escape": "Escape",
    "home": "Home",
    "end": "End",
    "pagedown": "PageDown",
    "pageup": "PageUp",
    "backspace": "BSpace",
    "enter": "Enter",
    "paste": "C-v",  # 粘贴

    # 组合键
    "ctrl_c": "C-c",
    "shift_up": "S-Up",
    "shift_down": "S-Down",
    "shift_tab": "RAW:\x1b[Z",  # Shift+Tab 原始转义序列
}
