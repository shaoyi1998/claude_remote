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

# 有效的 tmux 修饰键前缀
VALID_MODIFIERS = {'C', 'S', 'M'}

# 需要转换为原始转义序列的特殊按键
# tmux send-keys 对某些 Shift 组合键支持不好，需要使用原始转义序列
SPECIAL_KEY_TO_RAW = {
    'S-Tab': '\x1b[Z',      # Shift+Tab
    'S-Up': '\x1b[1;2A',    # Shift+Up
    'S-Down': '\x1b[1;2B',  # Shift+Down
    'S-Left': '\x1b[1;2D',  # Shift+Left
    'S-Right': '\x1b[1;2C', # Shift+Right
    'S-Home': '\x1b[1;2H',  # Shift+Home
    'S-End': '\x1b[1;2F',   # Shift+End
}

# 有效的按键名称
VALID_KEYS = {
    # 字母
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    # 数字
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    # 功能键
    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
    # 特殊键
    'Tab', 'Home', 'End', 'Insert', 'Delete', 'PageUp', 'PageDown',
    'Escape', 'Enter', 'BSpace', 'Up', 'Down', 'Left', 'Right',
}


def validate_tmux_key(key: str) -> bool:
    """
    验证 tmux 格式的按键是否有效

    支持格式:
    - 单键: 'a', 'F1', 'Enter'
    - 单修饰键: 'C-c', 'S-Tab', 'M-a'
    - 双修饰键: 'C-S-c', 'C-M-a'

    Args:
        key: tmux 格式的按键字符串

    Returns:
        bool: 是否为有效的 tmux 按键格式
    """
    if not key:
        return False

    parts = key.split('-')

    # 单键情况
    if len(parts) == 1:
        return parts[0] in VALID_KEYS

    # 组合键情况：最后一部分是按键，其余是修饰键
    key_part = parts[-1]
    modifiers = parts[:-1]

    # 验证按键
    if key_part not in VALID_KEYS:
        return False

    # 验证修饰键
    for mod in modifiers:
        if mod not in VALID_MODIFIERS:
            return False

    return True
