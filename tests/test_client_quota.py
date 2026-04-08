"""
测试客户端配额系统
"""

import pytest
import time
from core.client_quota import (
    QuotaManager,
    Quota,
    QuotaUsage,
    QuotaPeriod,
    ClientQuotaConfig,
    get_quota_manager,
    register_client_quotas,
    check_client_quota,
)


@pytest.fixture
def manager():
    """创建测试用配额管理器"""
    QuotaManager._instance = None
    QuotaManager._lock = __import__('threading').Lock()
    m = QuotaManager()
    yield m
    m._initialized = False
    QuotaManager._instance = None


class TestQuotaUsage:
    """QuotaUsage测试"""

    def test_creation(self):
        """创建使用记录"""
        quota = Quota(calls=100, period=QuotaPeriod.DAY, window_seconds=86400)
        usage = QuotaUsage(client_id="test", quota=quota)

        assert usage.current == 0
        assert not usage.is_exhausted()

    def test_consume(self):
        """消费配额"""
        quota = Quota(calls=10, period=QuotaPeriod.DAY, window_seconds=86400)
        usage = QuotaUsage(client_id="test", quota=quota)

        assert usage.consume(3) is True
        assert usage.current == 3

        assert usage.consume(5) is True
        assert usage.current == 8

        assert usage.consume(3) is False  # 超过
        assert usage.current == 8

    def test_can_consume(self):
        """检查是否可以消费"""
        quota = Quota(calls=10, period=QuotaPeriod.DAY, window_seconds=86400)
        usage = QuotaUsage(client_id="test", quota=quota)

        assert usage.can_consume(5) is True
        usage.consume(8)
        assert usage.can_consume(3) is False
        assert usage.can_consume(2) is True

    def test_get_remaining(self):
        """获取剩余配额"""
        quota = Quota(calls=100, period=QuotaPeriod.DAY, window_seconds=86400)
        usage = QuotaUsage(client_id="test", quota=quota)

        assert usage.get_remaining() == 100
        usage.consume(30)
        assert usage.get_remaining() == 70

    def test_get_usage_percent(self):
        """获取使用百分比"""
        quota = Quota(calls=100, period=QuotaPeriod.DAY, window_seconds=86400)
        usage = QuotaUsage(client_id="test", quota=quota)

        assert usage.get_usage_percent() == 0
        usage.consume(75)
        assert usage.get_usage_percent() == 75


class TestQuotaManager:
    """QuotaManager测试"""

    def test_singleton(self):
        """单例模式"""
        m1 = get_quota_manager()
        m2 = get_quota_manager()
        assert m1 is m2

    def test_register_client(self, manager):
        """注册客户端"""
        config = manager.register_client(
            client_id="client-1",
            daily=100,
            monthly=1000
        )

        assert config.client_id == "client-1"
        assert config.daily_quota.calls == 100
        assert config.monthly_quota.calls == 1000

    def test_unregister_client(self, manager):
        """注销客户端"""
        manager.register_client("client-1", daily=100)
        assert manager.unregister_client("client-1") is True
        assert manager.get_config("client-1") is None

    def test_whitelist(self, manager):
        """白名单"""
        manager.add_to_whitelist("trusted-client")
        assert manager.is_whitelisted("trusted-client") is True
        assert manager.is_whitelisted("untrusted-client") is False

        manager.remove_from_whitelist("trusted-client")
        assert manager.is_whitelisted("trusted-client") is False

    def test_check_and_consume_allowed(self, manager):
        """允许消费"""
        manager.register_client("client-1", daily=100)

        result = manager.check_and_consume("client-1")

        assert result["allowed"] is True

    def test_check_and_consume_denied(self, manager):
        """拒绝消费"""
        manager.register_client("client-1", daily=2)

        manager.check_and_consume("client-1")
        manager.check_and_consume("client-1")

        result = manager.check_and_consume("client-1")

        assert result["allowed"] is False
        assert result["denied_by"]["period"] == "daily"

    def test_whitelist_bypass(self, manager):
        """白名单绕过"""
        manager.register_client("client-1", daily=1)
        manager.add_to_whitelist("client-1")

        # 无限消费
        for _ in range(100):
            result = manager.check_and_consume("client-1")
            assert result["allowed"] is True

    def test_no_quota(self, manager):
        """无配额配置"""
        result = manager.check_and_consume("unknown-client")
        assert result["allowed"] is True

    def test_exempt_client(self, manager):
        """豁免客户端"""
        manager.register_client("client-1", daily=1)
        config = manager.get_config("client-1")
        config.exempt = True

        for _ in range(100):
            result = manager.check_and_consume("client-1")
            assert result["allowed"] is True

    def test_get_usage(self, manager):
        """获取使用情况"""
        manager.register_client("client-1", daily=100, monthly=1000)

        manager.check_and_consume("client-1")
        manager.check_and_consume("client-1")
        manager.check_and_consume("client-1")

        usage = manager.get_usage("client-1")

        assert "daily" in usage
        assert usage["daily"]["current"] == 3
        assert usage["daily"]["total_usage"] == 3

    def test_get_all_clients_usage(self, manager):
        """获取所有客户端使用"""
        manager.register_client("client-1", daily=100)
        manager.register_client("client-2", daily=100)

        manager.check_and_consume("client-1")
        manager.check_and_consume("client-2")

        all_usage = manager.get_all_clients_usage()

        assert "client-1" in all_usage
        assert "client-2" in all_usage

    def test_reset_usage(self, manager):
        """重置使用"""
        manager.register_client("client-1", daily=100)

        manager.check_and_consume("client-1")
        manager.check_and_consume("client-1")

        usage = manager.get_usage("client-1")
        assert usage["daily"]["current"] == 2

        manager.reset_usage("client-1", "daily")

        usage = manager.get_usage("client-1")
        assert usage["daily"]["current"] == 0


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_register_and_check(self):
        """注册并检查"""
        QuotaManager._instance = None
        manager = QuotaManager()

        register_client_quotas("test-client", daily=5)

        assert check_client_quota("test-client") is True
        assert check_client_quota("test-client") is True

    def test_convenience_exhausted(self):
        """便捷函数耗尽"""
        QuotaManager._instance = None
        manager = QuotaManager()

        register_client_quotas("test-client", daily=2)

        check_client_quota("test-client")
        check_client_quota("test-client")

        assert check_client_quota("test-client") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
