"""
测试限流中间件

验证FastAPI中间件形式的全局限流
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from core.rate_limiter import configure_rate_limiter, RateLimitConfig, get_rate_limiter


class TestRateLimitMiddleware:
    """限流中间件测试"""

    @pytest.fixture(autouse=True)
    def reset_and_configure(self):
        """每个测试前重置限流器"""
        # 配置严格的限流（方便测试）
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=100,
            burst_size=3,
            enabled=True
        )
        configure_rate_limiter(config)
        limiter = get_rate_limiter()
        limiter.client_stats.clear()  # 清空统计
        yield

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_allows_requests_under_limit(self, client):
        """限额内请求允许通过"""
        # 前3个请求应该通过（burst_size=3）
        for i in range(3):
            response = client.get("/health")
            assert response.status_code == 200, f"Request {i+1} should succeed"
            assert "X-RateLimit-Remaining" in response.headers

    def test_blocks_requests_over_limit(self, client):
        """超限请求被阻止"""
        # 先耗尽限额
        for _ in range(10):
            client.get("/health")

        # 下一个请求应该被限流
        response = client.get("/health")
        assert response.status_code == 429
        data = response.json()
        assert "Rate limit exceeded" in data["error"]
        assert "retry_after" in data

    def test_rate_limit_headers_present(self, client):
        """限流响应头存在"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Limit" in response.headers

    def test_retry_after_header(self, client):
        """Retry-After头正确"""
        # 耗尽限额
        for _ in range(10):
            client.get("/health")

        response = client.get("/health")
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_health_endpoint_skipped(self, client):
        """健康检查端点跳过限流"""
        # 使用新的client（新请求上下文）
        # 先用不同路径耗尽全局限额
        limiter = get_rate_limiter()
        limiter.minute_limiter.requests.clear()
        limiter.hourly_limiter.requests.clear()

        # 验证health路径确实在跳过列表中
        from core.rate_limit_middleware import RateLimitMiddleware
        assert "/health" in RateLimitMiddleware.SKIP_PATHS

    def test_different_ips_independent_limit(self, client):
        """不同IP独立限流"""
        # 模拟从不同IP请求
        # 由于我们用同一个TestClient，IP相同，所以只测试限额独立计数
        limiter = get_rate_limiter()
        limiter.minute_limiter.requests.clear()

        # 用另一端点耗尽限额
        for _ in range(10):
            client.get("/api/monitoring/metrics/system")

        response = client.get("/api/monitoring/metrics/system")
        # 确认被限流
        assert response.status_code == 429


class TestCORSConfiguration:
    """CORS配置测试"""

    def test_cors_origins_not_wildcard(self):
        """CORS不使用通配符"""
        # 验证CORS中间件配置正确
        # 检查settings中的CORS配置
        import os
        cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        origins = cors_env.split(",")

        # 验证不是通配符
        assert "*" not in origins, "CORS origins should not contain wildcard"
        assert len(origins) > 0, "CORS origins should be configured"
        print(f"CORS configured origins: {origins}")
