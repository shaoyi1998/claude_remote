"""
登录防爆破服务
"""
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Tuple

from config import settings


class LoginRateLimiter:
    """登录频率限制器"""

    def __init__(self):
        self.max_attempts = settings.login_max_attempts
        self.lockout_minutes = settings.login_lockout_minutes
        # {ip: (fail_count, first_fail_time, lockout_until)}
        self._attempts: Dict[str, Tuple[int, datetime, datetime | None]] = {}
        self._lock = Lock()

    def _get_client_ip(self, request) -> str:
        """获取客户端真实 IP"""
        # 检查反向代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 取第一个 IP（最原始的客户端 IP）
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接连接
        if request.client:
            return request.client.host

        return "unknown"

    def is_locked(self, ip: str) -> Tuple[bool, int]:
        """
        检查 IP 是否被锁定
        返回: (是否锁定, 剩余分钟数)
        """
        with self._lock:
            if ip not in self._attempts:
                return False, 0

            fail_count, first_fail_time, lockout_until = self._attempts[ip]

            if lockout_until is None:
                return False, 0

            if datetime.now() < lockout_until:
                remaining = (lockout_until - datetime.now()).total_seconds() / 60
                return True, int(remaining)

            # 锁定已过期，清除记录
            del self._attempts[ip]
            return False, 0

    def record_failure(self, ip: str) -> Tuple[int, bool]:
        """
        记录登录失败
        返回: (当前失败次数, 是否触发锁定)
        """
        with self._lock:
            now = datetime.now()

            if ip not in self._attempts:
                self._attempts[ip] = (1, now, None)
                return 1, False

            fail_count, first_fail_time, lockout_until = self._attempts[ip]

            # 如果已锁定，返回当前状态
            if lockout_until and now < lockout_until:
                return fail_count, True

            # 如果锁定已过期或超过重置时间窗口（24小时），重置计数
            if lockout_until or (now - first_fail_time) > timedelta(minutes=self.lockout_minutes):
                self._attempts[ip] = (1, now, None)
                return 1, False

            # 增加失败次数
            fail_count += 1

            if fail_count >= self.max_attempts:
                # 触发锁定
                lockout_until = now + timedelta(minutes=self.lockout_minutes)
                self._attempts[ip] = (fail_count, first_fail_time, lockout_until)
                return fail_count, True

            self._attempts[ip] = (fail_count, first_fail_time, None)
            return fail_count, False

    def reset(self, ip: str):
        """登录成功后重置计数"""
        with self._lock:
            if ip in self._attempts:
                del self._attempts[ip]

    def cleanup_expired(self):
        """清理过期记录"""
        with self._lock:
            now = datetime.now()
            expired_ips = []
            for ip, (fail_count, first_fail_time, lockout_until) in self._attempts.items():
                if lockout_until and now > lockout_until:
                    expired_ips.append(ip)
                elif not lockout_until and (now - first_fail_time) > timedelta(minutes=self.lockout_minutes):
                    expired_ips.append(ip)

            for ip in expired_ips:
                del self._attempts[ip]


# 全局单例
login_rate_limiter = LoginRateLimiter()
