"""
客户端配额系统 - Client Quota Management
==========================================

【功能】
1. 配额限制 - 按客户端ID设置调用上限
2. 配额追踪 - 记录每个客户端的使用量
3. 配额预警 - 达到阈值时发送告警
4. 配额重置 - 支持日/月/年周期重置
5. 配额豁免 - 白名单客户端不受限制

【使用场景】
- 限制免费用户每日API调用次数
- 按套餐控制企业用户配额
- 检测异常高频调用
"""

import time
from typing import Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class QuotaPeriod(Enum):
    """配额周期"""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


@dataclass
class Quota:
    """配额配置"""
    calls: int              # 最大调用次数
    period: QuotaPeriod     # 周期
    window_seconds: float   # 窗口秒数


@dataclass
class QuotaUsage:
    """配额使用记录"""
    client_id: str
    quota: Quota
    current: int = 0
    window_start: float = field(default_factory=time.time)
    total_usage: int = 0  # 累计使用（不重置）
    last_call_at: Optional[float] = None

    def is_exhausted(self) -> bool:
        """是否已用完"""
        self._check_window()
        return self.current >= self.quota.calls

    def _check_window(self):
        """检查窗口是否过期"""
        now = time.time()
        elapsed = now - self.window_start
        if elapsed >= self.quota.window_seconds:
            # 窗口重置
            self.current = 0
            self.window_start = now

    def can_consume(self, count: int = 1) -> bool:
        """是否可以消费"""
        self._check_window()
        return self.current + count <= self.quota.calls

    def consume(self, count: int = 1) -> bool:
        """消费配额

        Returns:
            True if consumed, False if quota exceeded
        """
        if not self.can_consume(count):
            return False

        self.current += count
        self.total_usage += count
        self.last_call_at = time.time()
        return True

    def get_remaining(self) -> int:
        """获取剩余配额"""
        self._check_window()
        return max(0, self.quota.calls - self.current)

    def get_usage_percent(self) -> float:
        """获取使用百分比"""
        if self.quota.calls == 0:
            return 0
        return min(100, (self.current / self.quota.calls) * 100)


@dataclass
class ClientQuotaConfig:
    """客户端配额配置"""
    client_id: str
    daily_quota: Optional[Quota] = None
    monthly_quota: Optional[Quota] = None
    annual_quota: Optional[Quota] = None
    enabled: bool = True
    exempt: bool = False  # 豁免（不受限制）
    warn_threshold: float = 0.8  # 预警阈值


class QuotaManager:
    """配额管理器

    【架构】
    - 按客户端ID存储配额配置
    - 滑动窗口追踪使用量
    - 支持多层级配额（日/月/年）
    - 白名单豁免
    """

    _instance: Optional['QuotaManager'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'QuotaManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._configs: Dict[str, ClientQuotaConfig] = {}
        self._usage: Dict[str, Dict[str, QuotaUsage]] = {}  # client_id -> {period: usage}
        self._whitelist: Set[str] = set()  # 白名单客户端ID
        self._config_lock = threading.Lock()
        self._usage_lock = threading.Lock()

        # 配额预警回调
        self._warning_callbacks: list = []

        self._initialized = True

    def set_whitelist(self, client_ids: Set[str]):
        """设置白名单"""
        with self._config_lock:
            self._whitelist = client_ids.copy()

    def add_to_whitelist(self, client_id: str):
        """添加到白名单"""
        with self._config_lock:
            self._whitelist.add(client_id)

    def remove_from_whitelist(self, client_id: str):
        """从白名单移除"""
        with self._config_lock:
            self._whitelist.discard(client_id)

    def is_whitelisted(self, client_id: str) -> bool:
        """检查是否在白名单"""
        with self._config_lock:
            return client_id in self._whitelist

    def register_client(
        self,
        client_id: str,
        daily: Optional[int] = None,
        monthly: Optional[int] = None,
        annual: Optional[int] = None,
        warn_threshold: float = 0.8
    ) -> ClientQuotaConfig:
        """注册客户端配额"""
        quotas = {}

        if daily:
            quotas['daily'] = Quota(
                calls=daily,
                period=QuotaPeriod.DAY,
                window_seconds=86400
            )

        if monthly:
            quotas['monthly'] = Quota(
                calls=monthly,
                period=QuotaPeriod.MONTH,
                window_seconds=2592000
            )

        if annual:
            quotas['annual'] = Quota(
                calls=annual,
                period=QuotaPeriod.YEAR,
                window_seconds=31536000
            )

        config = ClientQuotaConfig(
            client_id=client_id,
            daily_quota=quotas.get('daily'),
            monthly_quota=quotas.get('monthly'),
            annual_quota=quotas.get('annual'),
            warn_threshold=warn_threshold
        )

        with self._config_lock:
            self._configs[client_id] = config

        with self._usage_lock:
            self._usage[client_id] = {}

        logger.info(f"Registered quota for client {client_id}: {list(quotas.keys())}")
        return config

    def unregister_client(self, client_id: str) -> bool:
        """注销客户端"""
        with self._config_lock:
            if client_id in self._configs:
                del self._configs[client_id]

        with self._usage_lock:
            if client_id in self._usage:
                del self._usage[client_id]

        return True

    def get_config(self, client_id: str) -> Optional[ClientQuotaConfig]:
        """获取客户端配额配置"""
        with self._config_lock:
            return self._configs.get(client_id)

    def _get_or_create_usage(self, client_id: str, period_key: str, quota: Quota) -> QuotaUsage:
        """获取或创建使用记录"""
        with self._usage_lock:
            if client_id not in self._usage:
                self._usage[client_id] = {}

            if period_key not in self._usage[client_id]:
                self._usage[client_id][period_key] = QuotaUsage(
                    client_id=client_id,
                    quota=quota
                )

            return self._usage[client_id][period_key]

    def check_and_consume(self, client_id: str, count: int = 1) -> Dict[str, Any]:
        """检查并消费配额

        Returns:
            {
                "allowed": bool,
                "quota_type": str or None,
                "remaining": int,
                "total_remaining": int,
                "reason": str or None
            }
        """
        # 白名单检查
        if self.is_whitelisted(client_id):
            return {"allowed": True, "reason": "whitelisted"}

        # 配置检查
        config = self.get_config(client_id)
        if not config or not config.enabled:
            return {"allowed": True, "reason": "no_quota"}

        # 豁免检查
        if config.exempt:
            return {"allowed": True, "reason": "exempt"}

        results = []

        # 检查每个配额层级
        for period_key, quota in [
            ("daily", config.daily_quota),
            ("monthly", config.monthly_quota),
            ("annual", config.annual_quota)
        ]:
            if quota is None:
                continue

            usage = self._get_or_create_usage(client_id, period_key, quota)

            if usage.is_exhausted():
                results.append({
                    "period": period_key,
                    "allowed": False,
                    "remaining": 0,
                    "usage": usage.get_usage_percent()
                })
            elif not usage.can_consume(count):
                results.append({
                    "period": period_key,
                    "allowed": False,
                    "remaining": usage.get_remaining(),
                    "usage": usage.get_usage_percent()
                })
            else:
                results.append({
                    "period": period_key,
                    "allowed": True,
                    "remaining": usage.get_remaining() - count,
                    "usage": usage.get_usage_percent()
                })

        # 如果任何层级不允许，则拒绝
        denied = [r for r in results if not r["allowed"]]
        if denied:
            return {
                "allowed": False,
                "denied_by": denied[0],
                "results": results
            }

        # 消费配额
        for period_key, quota in [
            ("daily", config.daily_quota),
            ("monthly", config.monthly_quota),
            ("annual", config.annual_quota)
        ]:
            if quota is None:
                continue
            usage = self._get_or_create_usage(client_id, period_key, quota)
            usage.consume(count)

            # 预警检查
            if (usage.get_usage_percent() >= config.warn_threshold * 100 and
                usage.last_call_at and
                time.time() - usage.last_call_at < quota.window_seconds):
                self._trigger_warning(client_id, period_key, usage)

        # 返回成功结果
        return {
            "allowed": True,
            "results": results
        }

    def _trigger_warning(self, client_id: str, period: str, usage: QuotaUsage):
        """触发预警"""
        warning = {
            "client_id": client_id,
            "period": period,
            "usage_percent": usage.get_usage_percent(),
            "remaining": usage.get_remaining(),
            "total_usage": usage.total_usage
        }

        for callback in self._warning_callbacks:
            try:
                callback(warning)
            except Exception as e:
                logger.error(f"Warning callback error: {e}")

    def add_warning_callback(self, callback):
        """添加预警回调"""
        self._warning_callbacks.append(callback)

    def get_usage(self, client_id: str) -> Dict[str, Dict]:
        """获取客户端使用情况"""
        with self._usage_lock:
            usage_data = self._usage.get(client_id, {})

        return {
            period: {
                "current": u.current,
                "total_usage": u.total_usage,
                "remaining": u.get_remaining(),
                "usage_percent": u.get_usage_percent(),
                "window_start": u.window_start,
                "last_call_at": u.last_call_at
            }
            for period, u in usage_data.items()
        }

    def get_all_clients_usage(self) -> Dict[str, Dict]:
        """获取所有客户端使用情况"""
        with self._usage_lock:
            client_ids = list(self._usage.keys())

        return {
            client_id: self.get_usage(client_id)
            for client_id in client_ids
        }

    def reset_usage(self, client_id: str, period: Optional[str] = None):
        """重置使用量"""
        with self._usage_lock:
            if client_id not in self._usage:
                return

            if period:
                if period in self._usage[client_id]:
                    u = self._usage[client_id][period]
                    u.current = 0
                    u.window_start = time.time()
            else:
                # 重置所有周期
                for u in self._usage[client_id].values():
                    u.current = 0
                    u.window_start = time.time()


# ============ 便捷函数 ============

_manager: Optional[QuotaManager] = None


def get_quota_manager() -> QuotaManager:
    """获取配额管理器单例"""
    global _manager
    if _manager is None:
        _manager = QuotaManager()
    return _manager


def check_client_quota(client_id: str, count: int = 1) -> bool:
    """检查客户端配额（便捷函数）

    Returns:
        True if allowed, False if exceeded
    """
    return get_quota_manager().check_and_consume(client_id, count)["allowed"]


def register_client_quotas(
    client_id: str,
    daily: Optional[int] = None,
    monthly: Optional[int] = None,
    annual: Optional[int] = None
) -> ClientQuotaConfig:
    """注册客户端配额（便捷函数）"""
    return get_quota_manager().register_client(client_id, daily, monthly, annual)


# ============ 使用示例 ============
"""
【基本用法】

from core.client_quota import (
    get_quota_manager, register_client_quotas, check_client_quota
)

# 注册客户端配额
register_client_quotas(
    client_id="user-123",
    daily=1000,    # 每天1000次
    monthly=10000  # 每月10000次
)

# 检查配额
if check_client_quota("user-123"):
    # 执行API调用
    pass
else:
    # 配额超限
    pass

【获取使用情况】

manager = get_quota_manager()
usage = manager.get_usage("user-123")
print(f"Daily: {usage['daily']['remaining']} remaining")
print(f"Monthly: {usage['monthly']['remaining']} remaining")

【预警回调】

def on_warning(warning):
    print(f"Client {warning['client_id']} used {warning['usage_percent']}%")

manager = get_quota_manager()
manager.add_warning_callback(on_warning)

【白名单】

manager.add_to_whitelist("internal-service")
"""


if __name__ == "__main__":
    print("Testing ClientQuota...")

    manager = get_quota_manager()

    # 注册客户端
    manager.register_client(
        client_id="test-client",
        daily=10,
        monthly=100
    )

    # 消费配额
    for i in range(12):
        result = manager.check_and_consume("test-client")
        print(f"Call {i+1}: allowed={result['allowed']}")

    # 查看使用情况
    usage = manager.get_usage("test-client")
    print(f"Usage: {usage}")

    print("\nClientQuota OK")
