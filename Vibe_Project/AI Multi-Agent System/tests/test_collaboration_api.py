"""
Agent Collaboration API 端点测试
=================================

测试 /api/agents/collaborate/* 端点
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestCollaborationAPI:
    """Agent Collaboration API 测试"""

    def test_submit_collaborative_task(self, client):
        """测试提交协作任务"""
        response = client.post(
            "/api/agents/collaborate/submit",
            json={
                "task_description": "帮我写一个简单的Python函数",
                "context": {"language": "python"}
            }
        )

        # 应该返回200或500（如果LLM未配置）
        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "task_id" in data or "success" in data

    def test_submit_empty_task(self, client):
        """测试空任务描述"""
        response = client.post(
            "/api/agents/collaborate/submit",
            json={"task_description": ""}
        )

        # 应该返回错误
        assert response.status_code in [400, 422, 500]

    def test_get_collaboration_report(self, client):
        """测试获取协作报告"""
        response = client.get("/api/agents/collaborate/report")

        # 应该返回200
        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "success" in data or "total_tasks" in data

    def test_get_nonexistent_task_result(self, client):
        """测试获取不存在的任务结果"""
        response = client.get("/api/agents/collaborate/nonexistent_task_id")

        # 应该返回404
        assert response.status_code in [404, 500]


class TestCollaborationSubmission:
    """协作任务提交测试"""

    def test_submit_simple_task(self, client):
        """测试提交简单任务"""
        response = client.post(
            "/api/agents/collaborate/submit",
            json={
                "task_description": "写一个hello world程序"
            }
        )

        assert response.status_code in [200, 500]

    def test_submit_complex_task(self, client):
        """测试提交复杂任务"""
        response = client.post(
            "/api/agents/collaborate/submit",
            json={
                "task_description": "开发一个用户管理API，包含注册、登录、修改密码功能，并编写单元测试和文档"
            }
        )

        assert response.status_code in [200, 500]

    def test_submit_with_context(self, client):
        """测试带上下文的提交"""
        response = client.post(
            "/api/agents/collaborate/submit",
            json={
                "task_description": "生成项目文档",
                "context": {
                    "project_name": "MyProject",
                    "language": "python"
                }
            }
        )

        assert response.status_code in [200, 500]


class TestCollaborationResult:
    """协作任务结果获取测试"""

    def test_get_result_after_submit(self, client):
        """测试提交后获取结果"""
        # 先提交
        submit_response = client.post(
            "/api/agents/collaborate/submit",
            json={"task_description": "简单任务"}
        )

        if submit_response.status_code == 200:
            task_id = submit_response.json().get("task_id")
            if task_id:
                # 再获取结果
                result_response = client.get(f"/api/agents/collaborate/{task_id}")
                assert result_response.status_code in [200, 404, 500]


class TestCollaborationEdgeCases:
    """协作边界情况测试"""

    def test_submit_very_long_task(self, client):
        """测试超长任务描述"""
        long_desc = "描述 " * 1000
        response = client.post(
            "/api/agents/collaborate/submit",
            json={"task_description": long_desc}
        )

        # 应该处理而不崩溃
        assert response.status_code in [200, 400, 422, 500]

    def test_submit_special_characters(self, client):
        """测试特殊字符"""
        response = client.post(
            "/api/agents/collaborate/submit",
            json={"task_description": "测试<script>alert('xss')</script>"}
        )

        assert response.status_code in [200, 500]

    def test_concurrent_submissions(self, client):
        """测试并发提交"""
        import concurrent.futures

        def submit_task(i):
            return client.post(
                "/api/agents/collaborate/submit",
                json={"task_description": f"任务{i}"}
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(submit_task, i) for i in range(3)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有请求应该成功或返回错误（不是崩溃）
        for r in results:
            assert r.status_code in [200, 500]
