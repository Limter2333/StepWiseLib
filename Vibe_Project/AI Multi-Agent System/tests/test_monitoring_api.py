"""
Monitoring API 测试
=================

测试 /api/monitoring/* 端点
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestMonitoringSystemMetrics:
    """系统指标端点测试"""

    def test_get_system_metrics(self, client):
        """测试获取系统指标"""
        response = client.get("/api/monitoring/metrics/system")
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "samples" in data
        assert "cpu_avg" in data
        assert "memory_avg" in data

    def test_get_system_metrics_with_duration(self, client):
        """测试指定时间窗口"""
        response = client.get("/api/monitoring/metrics/system?duration_seconds=120")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "120s"

    def test_collect_system_metrics(self, client):
        """测试手动收集指标"""
        response = client.get("/api/monitoring/metrics/system/collect")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "cpu_percent" in data
        assert "memory_percent" in data


class TestMonitoringAgentMetrics:
    """Agent指标端点测试"""

    def test_get_agents_metrics(self, client):
        """测试获取所有Agent指标"""
        response = client.get("/api/monitoring/metrics/agents")
        assert response.status_code == 200
        # 返回字典
        data = response.json()
        assert isinstance(data, dict)

    def test_get_agent_leaderboard(self, client):
        """测试Agent排行"""
        response = client.get("/api/monitoring/metrics/agents/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_agent_leaderboard_with_params(self, client):
        """测试Agent排行参数"""
        response = client.get("/api/monitoring/metrics/agents/leaderboard?sort_by=success_rate&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestMonitoringBusinessMetrics:
    """业务指标端点测试"""

    def test_get_business_metrics(self, client):
        """测试获取业务指标"""
        response = client.get("/api/monitoring/metrics/business")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "total_tasks" in data
        assert "completed_tasks" in data

    def test_record_task(self, client):
        """测试记录任务"""
        response = client.post("/api/monitoring/metrics/business/task?success=true")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_record_query(self, client):
        """测试记录查询"""
        response = client.post("/api/monitoring/metrics/business/query")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_sessions(self, client):
        """测试更新会话数"""
        response = client.post("/api/monitoring/metrics/business/sessions?count=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestMonitoringHealth:
    """健康检查端点测试"""

    def test_get_overall_health(self, client):
        """测试整体健康状态"""
        response = client.get("/api/monitoring/health/overall")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "healthy_count" in data
        assert "degraded_count" in data
        assert "down_count" in data

    def test_get_components_health(self, client):
        """测试组件健康状态列表"""
        response = client.get("/api/monitoring/health/components")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_component_health(self, client):
        """测试更新组件健康状态"""
        response = client.post(
            "/api/monitoring/health/components/test_component?status=healthy&response_time_ms=50.0"
        )
        assert response.status_code == 200


class TestMonitoringAlerts:
    """告警端点测试"""

    def test_get_active_alerts(self, client):
        """测试获取当前告警"""
        response = client.get("/api/monitoring/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_alert_history(self, client):
        """测试获取告警历史"""
        response = client.get("/api/monitoring/alerts/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_alert_history_with_limit(self, client):
        """测试告警历史限制"""
        response = client.get("/api/monitoring/alerts/history?limit=10")
        assert response.status_code == 200

    def test_get_alert_rules(self, client):
        """测试获取告警规则"""
        response = client.get("/api/monitoring/alerts/rules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 7  # 至少7条默认规则

    def test_create_alert_rule(self, client):
        """测试创建告警规则"""
        rule = {
            "name": "test_rule",
            "metric_type": "cpu",
            "threshold": 90.0,
            "comparison": "gte",
            "duration_seconds": 60,
            "severity": "warning",
            "enabled": True
        }
        response = client.post("/api/monitoring/alerts/rules", json=rule)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_alert_status(self, client):
        """测试获取告警状态摘要"""
        response = client.get("/api/monitoring/alerts/status")
        assert response.status_code == 200
        data = response.json()
        assert "total_rules" in data
        assert "enabled_rules" in data
        assert "active_alerts" in data


class TestMonitoringReport:
    """完整报告端点测试"""

    def test_get_full_report(self, client):
        """测试获取完整监控报告"""
        response = client.get("/api/monitoring/report")
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "system" in data
        assert "agents" in data
        assert "agent_leaderboard" in data
        assert "business" in data
        assert "health" in data
        assert "active_alerts" in data


class TestMonitoringTrack:
    """追踪端点测试"""

    def test_track_agent_request(self, client):
        """测试追踪Agent请求"""
        response = client.post(
            "/api/monitoring/track/agent/test_agent?duration_ms=100&success=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestUsageStatsAPI:
    """API使用统计端点测试"""

    @pytest.fixture(autouse=True)
    def clear_stats(self):
        """每个测试前清空统计"""
        from monitoring.usage_stats import get_usage_stats
        stats = get_usage_stats()
        stats.clear()
        yield
        stats.clear()

    def test_record_usage(self, client):
        """POST /api/monitoring/usage/record 记录API调用"""
        response = client.post(
            "/api/monitoring/usage/record",
            json={
                "endpoint": "/api/test/record",
                "method": "POST",
                "duration_ms": 150.5,
                "token_count": 500,
                "status_code": 200,
                "session_id": "test-session"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "cost_estimate_usd" in data
        assert data["cost_estimate_usd"] > 0

    def test_get_total_stats(self, client):
        """GET /api/monitoring/usage/total 获取总统计"""
        client.post("/api/monitoring/usage/record", json={
            "endpoint": "/api/test/total",
            "method": "GET",
            "duration_ms": 100.0,
            "token_count": 200,
            "status_code": 200
        })

        response = client.get("/api/monitoring/usage/total")
        assert response.status_code == 200
        data = response.json()
        assert data["total_calls"] == 1
        assert data["total_tokens"] == 200

    def test_get_endpoint_stats(self, client):
        """GET /api/monitoring/usage/endpoints 获取端点统计"""
        response = client.get("/api/monitoring/usage/endpoints")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data

    def test_get_session_stats(self, client):
        """GET /api/monitoring/usage/session/{session_id} 获取会话统计"""
        session_id = "test-session-api"
        client.post("/api/monitoring/usage/record", json={
            "endpoint": "/api/test/session",
            "method": "POST",
            "duration_ms": 100.0,
            "token_count": 300,
            "status_code": 200,
            "session_id": session_id
        })

        response = client.get(f"/api/monitoring/usage/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["call_count"] == 1

    def test_clear_usage(self, client):
        """DELETE /api/monitoring/usage/clear 清空统计"""
        client.post("/api/monitoring/usage/record", json={
            "endpoint": "/api/test/clear",
            "method": "DELETE",
            "duration_ms": 50.0,
            "token_count": 100,
            "status_code": 200
        })

        response = client.delete("/api/monitoring/usage/clear")
        assert response.status_code == 200

        total = client.get("/api/monitoring/usage/total")
        assert total.json()["total_calls"] == 0

    def test_cost_estimate(self, client):
        """GET /api/monitoring/usage/cost/estimate 成本估算"""
        response = client.get(
            "/api/monitoring/usage/cost/estimate",
            params={"input_tokens": 1000000, "output_tokens": 500000}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cost_usd"] == 7.50


class TestPrometheusMetricsExport:
    """Prometheus指标导出端点测试"""

    def test_get_prometheus_metrics(self, client):
        """测试Prometheus格式指标"""
        response = client.get("/api/monitoring/metrics/prometheus")
        assert response.status_code == 200
        # 内容应该是Prometheus格式的指标
        content = response.text
        assert "python_gc" in content or "process_" in content or "system_" in content or "# HELP" in content or "# TYPE" in content

    def test_export_metrics_json(self, client):
        """测试JSON格式导出"""
        response = client.get("/api/monitoring/metrics/export?format=json")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "timestamp" in data or "metrics" in data

    def test_export_metrics_prometheus(self, client):
        """测试Prometheus格式导出"""
        response = client.get("/api/monitoring/metrics/export?format=prometheus")
        assert response.status_code == 200
        # Prometheus格式应该是文本
        content = response.text
        assert "# HELP" in content or "# TYPE" in content or "python_gc" in content
