"""
平台检测工具
仅支持 Linux (包括 WSL)
"""
import platform
import sys
import os

_terminal_service_instance = None


def is_linux() -> bool:
    """检测是否是 Linux 系统 (包括 WSL)"""
    return platform.system() == 'Linux'


def is_wsl() -> bool:
    """检测是否是 WSL 环境"""
    if not is_linux():
        return False
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False


def get_terminal_service():
    """获取终端服务 (仅支持 Linux/WSL)"""
    global _terminal_service_instance

    if _terminal_service_instance is None:
        if is_linux():
            from services.tmux_service import TmuxService
            _terminal_service_instance = TmuxService()
        else:
            raise RuntimeError(
                f"不支持的操作系统: {platform.system()}。"
                f"本系统仅支持 Linux (包括 WSL)。"
            )

    return _terminal_service_instance


def is_root():
    """检测是否是 root 用户"""
    return os.geteuid() == 0
