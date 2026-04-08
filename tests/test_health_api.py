"""
Health API 端点测试
====================

【测试改进 - Phase 1 Critical】
覆盖 /health, /health/ready, /health/stats 端点
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestHealthAPI:
    """Health API 测试套件"""

    def test_health_check(self, client):
        """测试基本健康检查端点"""
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_health_check_response_time(self, client):
        """测试健康检查响应时间 < 100ms"""
        import time
        start = time.time()
        response = client.get("/health/")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 100, f"响应时间 {elapsed}ms 超过 100ms 阈值"

    def test_ready_check_healthy(self, client):
        """测试就绪检查 - 所有服务正常"""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        # 验证组件状态
        assert "components" in data or "status" in data

    def test_ready_check_components(self, client):
        """测试各组件就绪状态"""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        # 验证必要组件
        if "components" in data:
            for component in data["components"]:
                assert "name" in component
                assert "status" in component
                assert component["status"] in ["healthy", "degraded", "unhealthy"]

    def test_stats_endpoint(self, client):
        """测试统计信息端点"""
        response = client.get("/health/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证统计数据结构
        assert isinstance(data, dict)

    def test_stats_contains_metrics(self, client):
        """测试统计数据包含必要指标"""
        response = client.get("/health/stats")

        assert response.status_code == 200
        data = response.json()

        # 验证统计指标
        assert "requests" in data or "uptime" in data or "memory" in data

    def test_health_unauthorized_bypass(self, client):
        """测试健康检查不需要认证"""
        # 健康检查应该公开可访问
        response = client.get("/health/")

        assert response.status_code == 200

    def test_health_json_content_type(self, client):
        """测试返回JSON格式"""
        response = client.get("/health/")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_multiple_calls(self, client):
        """测试连续多次调用"""
        for _ in range(5):
            response = client.get("/health/")
            assert response.status_code == 200

    def test_ready_with_query_params(self, client):
        """测试带查询参数的就绪检查"""
        response = client.get("/health/ready?detailed=true")

        # 应该忽略额外参数但仍返回200
        assert response.status_code == 200

    def test_stats_with_accept_header(self, client):
        """测试带Accept头的统计请求"""
        response = client.get(
            "/health/stats",
            headers={"Accept": "application/json"}
        )

        assert response.status_code == 200


class TestHealthEdgeCases:
    """健康检查边界情况测试"""

    def test_health_invalid_path(self, client):
        """测试无效路径"""
        response = client.get("/health/invalid")

        assert response.status_code == 404

    def test_health_trailing_slash(self, client):
        """测试尾部斜杠"""
        response1 = client.get("/health")
        response2 = client.get("/health/")

        # 两个都应该工作
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestPingEndpoint:
    """Ping 端点测试（用于存活探针）"""

    def test_ping_returns_pong(self, client):
        """测试 ping 返回 pong"""
        response = client.get("/health/ping")

        assert response.status_code == 200
        data = response.json()
        assert data["ping"] == "pong"
        assert "timestamp" in data

    def test_ping_multiple_calls(self, client):
        """测试连续 ping 调用"""
        for _ in range(3):
            response = client.get("/health/ping")
            assert response.status_code == 200
            assert response.json()["ping"] == "pong"


class TestUptimeEndpoint:
    """服务运行时间端点测试"""

    def test_uptime_returns_seconds(self, client):
        """测试 uptime 返回秒数"""
        response = client.get("/health/uptime")

        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "uptime_human" in data
        assert "started_at" in data
        assert "current_time" in data
        assert data["uptime_seconds"] >= 0

    def test_uptime_increases(self, client):
        """测试 uptime 随时间增加"""
        import time
        response1 = client.get("/health/uptime")
        time.sleep(0.1)
        response2 = client.get("/health/uptime")

        assert response1.json()["uptime_seconds"] <= response2.json()["uptime_seconds"]
