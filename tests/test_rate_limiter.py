"""
测试API限流器

验证令牌桶、滑动窗口、限流中间件功能
"""

import pytest
import time
from core.rate_limiter import (
    TokenBucket,
    SlidingWindowCounter,
    RateLimiter,
    RateLimitConfig,
    RateLimitResult,
    get_rate_limiter,
    configure_rate_limiter
)


class TestTokenBucket:
    """令牌桶测试"""

    def test_bucket_initialization(self):
        """桶初始为满"""
        bucket = TokenBucket(rate=1.0, capacity=5)
        assert bucket.tokens == 5.0

    def test_consume_success(self):
        """消费令牌成功"""
        bucket = TokenBucket(rate=1.0, capacity=5)
        allowed, wait = bucket.consume(1)
        assert allowed is True
        assert wait == 0.0
        assert bucket.tokens == 4.0

    def test_consume_multiple(self):
        """消费多个令牌"""
        bucket = TokenBucket(rate=1.0, capacity=5)
        allowed, wait = bucket.consume(3)
        assert allowed is True
        assert bucket.tokens == 2.0

    def test_consume_exhausted(self):
        """令牌耗尽时拒绝"""
        bucket = TokenBucket(rate=1.0, capacity=2)
        bucket.consume(1)  # 剩1
        bucket.consume(1)  # 剩0
        allowed, wait = bucket.consume(1)  # 拒绝
        assert allowed is False
        assert wait > 0

    def test_bucket_refills(self):
        """令牌随时间补充"""
        bucket = TokenBucket(rate=10.0, capacity=5)
        bucket.consume(5)  # 耗尽
        assert bucket.tokens == 0.0

        time.sleep(0.2)  # 等待补充
        allowed, _ = bucket.consume(1)
        assert allowed is True
        assert bucket.tokens < 5.0  # 不会超过容量


class TestSlidingWindowCounter:
    """滑动窗口计数器测试"""

    def test_allows_under_limit(self):
        """限额内允许"""
        counter = SlidingWindowCounter(window_size_seconds=60, max_requests=5)

        class MockRequest:
            def __init__(self):
                pass

        for i in range(5):
            allowed, remaining = counter.is_allowed("test_client")
            assert allowed is True
            assert remaining == 4 - i

    def test_blocks_over_limit(self):
        """超限时拒绝"""
        counter = SlidingWindowCounter(window_size_seconds=60, max_requests=3)

        for i in range(3):
            counter.is_allowed("test_client")

        allowed, remaining = counter.is_allowed("test_client")
        assert allowed is False
        assert remaining == 0

    def test_different_clients_independent(self):
        """不同客户端独立计数"""
        counter = SlidingWindowCounter(window_size_seconds=60, max_requests=2)

        counter.is_allowed("client1")
        counter.is_allowed("client1")
        allowed, _ = counter.is_allowed("client1")  # client1已达上限

        allowed2, remaining2 = counter.is_allowed("client2")  # client2独立
        assert allowed is False
        assert allowed2 is True
        assert remaining2 == 1

    def test_reset_clears_client(self):
        """重置清除客户端"""
        counter = SlidingWindowCounter(window_size_seconds=60, max_requests=2)
        counter.is_allowed("client1")
        counter.is_allowed("client1")

        counter.reset("client1")

        allowed, remaining = counter.is_allowed("client1")
        assert allowed is True
        assert remaining == 1


class TestRateLimiter:
    """限流器测试"""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=100,
            burst_size=3
        ))

    @pytest.fixture
    def mock_request(self):
        class MockClient:
            host = "192.168.1.100"
        class MockRequest:
            client = MockClient()
            headers = {}
        return MockRequest()

    def test_allows_under_limit(self, limiter, mock_request):
        """限额内允许（burst=3，所以前3个通过）"""
        for i in range(3):
            result = limiter.check_rate_limit(mock_request)
            assert result.allowed is True, f"Request {i+1} should be allowed"

    def test_blocks_over_limit(self, limiter, mock_request):
        """超限时拒绝"""
        for i in range(10):
            limiter.check_rate_limit(mock_request)

        result = limiter.check_rate_limit(mock_request)
        assert result.allowed is False
        assert result.limit_type in ["minute", "hour", "burst"]

    def test_whitelisted_bypasses(self, limiter, mock_request):
        """白名单跳过限流"""
        limiter.add_to_whitelist("ip:192.168.1.100")

        for i in range(100):
            result = limiter.check_rate_limit(mock_request)
            assert result.allowed is True

    def test_stats_tracking(self, limiter, mock_request):
        """统计追踪"""
        limiter.check_rate_limit(mock_request)
        limiter.check_rate_limit(mock_request)

        stats = limiter.get_client_stats(mock_request)
        assert stats["total_requests"] == 2
        assert stats["blocked_requests"] == 0

    def test_blocked_stats_tracking(self, limiter, mock_request):
        """阻止统计"""
        # 耗尽限额
        for _ in range(10):
            limiter.check_rate_limit(mock_request)

        stats = limiter.get_client_stats(mock_request)
        assert stats["blocked_requests"] > 0

    def test_get_all_stats(self, limiter, mock_request):
        """全局统计"""
        limiter.check_rate_limit(mock_request)

        stats = limiter.get_all_stats()
        assert "total_clients" in stats
        assert "total_requests" in stats
        assert "total_blocked" in stats


class TestRateLimitConfig:
    """限流配置测试"""

    def test_default_config(self):
        """默认配置"""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_size == 10
        assert config.enabled is True

    def test_custom_config(self):
        """自定义配置"""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5,
            enabled=False
        )
        assert config.requests_per_minute == 10
        assert config.enabled is False


class TestSingletonFunctions:
    """单例函数测试"""

    def test_configure_and_get(self):
        """配置和获取"""
        config = RateLimitConfig(requests_per_minute=1)
        configure_rate_limiter(config)

        limiter = get_rate_limiter()
        assert limiter.config.requests_per_minute == 1

    def test_get_returns_same_instance(self):
        """获取同一实例"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2
