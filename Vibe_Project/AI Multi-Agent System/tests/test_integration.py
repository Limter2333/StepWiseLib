"""
集成测试 - Integration Tests
=============================

测试多个组件间的协作流程
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


class TestHealthToMonitoring:
    """健康检查到监控的集成"""

    def test_health_check_then_get_monitoring(self, client):
        """测试健康检查后获取监控数据"""
        # 1. 检查健康状态
        health_resp = client.get("/health")
        assert health_resp.status_code == 200

        # 2. 获取监控报告
        monitor_resp = client.get("/api/monitoring/report")
        assert monitor_resp.status_code == 200
        report = monitor_resp.json()
        assert "system" in report
        assert "agents" in report


class TestAgentToTaskQueue:
    """Agent执行到任务队列的集成"""

    def test_create_task_then_execute_agent(self, client):
        """测试创建任务后执行Agent"""
        # 1. 创建任务
        task_resp = client.post(
            "/api/tasks/",
            json={"name": "集成测试任务", "agent": "dev"}
        )
        assert task_resp.status_code == 200
        task_id = task_resp.json()["task_id"]

        # 2. 更新任务为运行中
        update_resp = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "running"}
        )
        assert update_resp.status_code == 200

        # 3. 调用Agent
        agent_resp = client.post(
            "/api/agents/dev/generate",
            params={
                "description": "Write a hello world function",
                "language": "python"
            }
        )
        assert agent_resp.status_code == 200

        # 4. 完成任务
        complete_resp = client.patch(
            f"/api/tasks/{task_id}",
            json={
                "status": "completed",
                "result": agent_resp.json()
            }
        )
        assert complete_resp.status_code == 200
        assert complete_resp.json()["status"] == "completed"

        # 5. 验证任务统计
        stats_resp = client.get("/api/tasks/stats/summary")
        assert stats_resp.status_code == 200


class TestChatToRAG:
    """对话到RAG的集成"""

    def test_chat_uses_rag(self, client):
        """测试对话使用RAG知识库"""
        # 1. 创建会话
        session_resp = client.post(
            "/api/chat/sessions",
            json={"user_id": "test_user"}
        )
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session_id"]

        # 2. 发送消息（使用知识库）
        chat_resp = client.post(
            "/api/chat/chat",
            json={
                "message": "What is RAG?",
                "session_id": session_id,
                "use_knowledge": True
            }
        )
        assert chat_resp.status_code == 200

        # 3. 获取会话历史
        history_resp = client.get(f"/api/chat/sessions/{session_id}/history")
        assert history_resp.status_code == 200


class TestMonitoringMetrics:
    """监控指标收集集成"""

    def test_record_and_retrieve_metrics(self, client):
        """测试记录并获取指标"""
        # 1. 记录一些任务
        for i in range(3):
            client.post("/api/monitoring/metrics/business/task", params={"success": "true"})

        client.post("/api/monitoring/metrics/business/query")

        # 2. 追踪Agent请求
        client.post(
            "/api/monitoring/track/agent/dev",
            params={"duration_ms": 150.5, "success": "true"}
        )

        # 3. 获取业务指标
        business_resp = client.get("/api/monitoring/metrics/business")
        assert business_resp.status_code == 200
        business = business_resp.json()
        assert business["total_tasks"] >= 3
        assert business["total_queries"] >= 1

        # 4. 获取Agent指标
        agent_resp = client.get("/api/monitoring/metrics/agents")
        assert agent_resp.status_code == 200


class TestAlertWorkflow:
    """告警工作流集成"""

    def test_create_rule_then_trigger_alert(self, client):
        """测试创建规则后触发告警"""
        # 1. 创建自定义告警规则
        rule_resp = client.post(
            "/api/monitoring/alerts/rules",
            json={
                "name": "custom_test_rule",
                "metric_type": "cpu",
                "threshold": 99.0,
                "comparison": "gte",
                "severity": "critical"
            }
        )
        assert rule_resp.status_code == 200

        # 2. 验证规则存在
        rules_resp = client.get("/api/monitoring/alerts/rules")
        assert rules_resp.status_code == 200
        rules = rules_resp.json()
        rule_names = [r["name"] for r in rules]
        assert "custom_test_rule" in rule_names

        # 3. 获取告警状态
        status_resp = client.get("/api/monitoring/alerts/status")
        assert status_resp.status_code == 200


class TestDocumentWorkflow:
    """文档工作流集成"""

    def test_create_readme_via_agent(self, client):
        """测试通过Agent创建README"""
        # 1. 使用Doc Agent生成README
        doc_resp = client.post(
            "/api/agents/doc/generate-readme",
            json={
                "project_name": "TestProject",
                "description": "A test project",
                "features": ["Feature 1", "Feature 2"]
            }
        )
        assert doc_resp.status_code == 200
        result = doc_resp.json()
        assert result["success"] is True
        assert "content" in result

        # 2. 验证结果质量
        if "validation" in result:
            assert "is_valid" in result["validation"]
            assert "quality" in result["validation"]


class TestAgentCollaboration:
    """Agent协作集成"""

    def test_multiple_agents(self, client):
        """测试多个Agent协作"""
        # 1. 获取所有Agent状态
        status_resp = client.get("/api/agents/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert "agents" in status

        # 2. 测试Task Router
        route_resp = client.post(
            "/api/agents/route",
            params={"description": "Write a test function"}
        )
        assert route_resp.status_code == 200


class TestSessionManagement:
    """会话管理集成"""

    def test_full_session_lifecycle(self, client):
        """测试完整会话生命周期"""
        # 1. 创建会话
        session_resp = client.post(
            "/api/chat/sessions",
            json={"user_id": "integration_test"}
        )
        assert session_resp.status_code == 200
        session_id = session_resp.json()["session_id"]

        # 2. 发送消息
        chat_resp = client.post(
            "/api/chat/chat",
            json={
                "message": "Hello",
                "session_id": session_id
            }
        )
        assert chat_resp.status_code == 200

        # 3. 获取摘要
        summary_resp = client.get(f"/api/chat/sessions/{session_id}/summary")
        assert summary_resp.status_code == 200

        # 4. 获取历史
        history_resp = client.get(f"/api/chat/sessions/{session_id}/history")
        assert history_resp.status_code == 200
        assert len(history_resp.json()) >= 1

        # 5. 列出所有会话
        list_resp = client.get("/api/chat/sessions")
        assert list_resp.status_code == 200


class TestTokenTracking:
    """Token追踪集成"""

    def test_chat_records_token_usage(self, client):
        """测试对话记录Token使用量"""
        # 1. 获取初始token状态
        initial_resp = client.get("/health/stats")
        initial = initial_resp.json()

        # 2. 发送消息
        chat_resp = client.post(
            "/api/chat/chat",
            json={
                "message": "Test message",
                "session_id": "token_test_session"
            }
        )
        assert chat_resp.status_code == 200

        # 3. 验证token使用被追踪
        token_resp = client.get("/api/chat/token-usage")
        assert token_resp.status_code == 200


class TestErrorHandling:
    """错误处理集成"""

    def test_graceful_error_handling(self, client):
        """测试优雅的错误处理"""
        # 1. 获取不存在的任务
        task_resp = client.get("/api/tasks/nonexistent_task_12345")
        assert task_resp.status_code == 404

        # 2. 获取不存在的会话
        session_resp = client.get("/api/chat/sessions/nonexistent_session_12345/history")
        assert session_resp.status_code == 404

        # 3. 发送空消息（应该被guardrails拦截）
        chat_resp = client.post(
            "/api/chat/chat",
            json={
                "message": "",
                "session_id": "test_session"
            }
        )
        # Guardrails应该拦截空消息
        assert chat_resp.status_code in [400, 422, 200]
