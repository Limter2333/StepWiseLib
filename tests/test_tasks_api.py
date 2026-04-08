"""
Task Queue API 测试
=================

测试 /api/tasks/* 端点
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


class TestTaskCreation:
    """任务创建测试"""

    def test_create_task(self, client):
        """测试创建任务"""
        response = client.post(
            "/api/tasks/",
            json={
                "name": "Test Task",
                "description": "A test task",
                "priority": "normal",
                "agent": "dev"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["name"] == "Test Task"
        assert data["status"] == "pending"

    def test_create_task_with_priority(self, client):
        """测试创建高优先级任务"""
        response = client.post(
            "/api/tasks/",
            json={
                "name": "Urgent Task",
                "priority": "critical",
                "agent": "dev"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "critical"


class TestTaskRetrieval:
    """任务获取测试"""

    def test_get_task(self, client):
        """测试获取任务"""
        # 先创建
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Get Test", "agent": "doc"}
        )
        task_id = create_resp.json()["task_id"]

        # 再获取
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id

    def test_get_nonexistent_task(self, client):
        """测试获取不存在的任务"""
        response = client.get("/api/tasks/nonexistent_id")
        assert response.status_code == 404


class TestTaskList:
    """任务列表测试"""

    def test_list_tasks(self, client):
        """测试列出任务"""
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_tasks_with_status_filter(self, client):
        """测试状态过滤"""
        # 创建几个任务
        for i in range(3):
            client.post("/api/tasks/", json={"name": f"Task {i}", "agent": "dev"})

        # 只获取pending状态
        response = client.get("/api/tasks/?status=pending")
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["status"] == "pending"

    def test_list_tasks_with_limit(self, client):
        """测试数量限制"""
        response = client.get("/api/tasks/?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5


class TestTaskUpdate:
    """任务更新测试"""

    def test_update_task_status(self, client):
        """测试更新任务状态"""
        # 创建任务
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Update Test", "agent": "test"}
        )
        task_id = create_resp.json()["task_id"]

        # 更新状态
        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "running"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["started_at"] is not None

    def test_update_task_progress(self, client):
        """测试更新任务进度"""
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Progress Test", "agent": "dev"}
        )
        task_id = create_resp.json()["task_id"]

        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"progress": 0.5}
        )
        assert response.status_code == 200
        assert response.json()["progress"] == 0.5

    def test_update_task_to_completed(self, client):
        """测试完成任务"""
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Complete Test", "agent": "dev"}
        )
        task_id = create_resp.json()["task_id"]

        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "completed", "result": {"output": "done"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        assert data["result"] == {"output": "done"}

    def test_update_task_with_error(self, client):
        """测试任务失败"""
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Fail Test", "agent": "dev"}
        )
        task_id = create_resp.json()["task_id"]

        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "failed", "error": "Something went wrong"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] == "Something went wrong"

    def test_update_nonexistent_task(self, client):
        """测试更新不存在的任务"""
        response = client.patch(
            "/api/tasks/nonexistent",
            json={"status": "running"}
        )
        assert response.status_code == 404


class TestTaskDelete:
    """任务删除测试"""

    def test_delete_task(self, client):
        """测试删除任务"""
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Delete Test", "agent": "dev"}
        )
        task_id = create_resp.json()["task_id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200

        # 验证已删除
        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_task(self, client):
        """测试删除不存在的任务"""
        response = client.delete("/api/tasks/nonexistent")
        assert response.status_code == 404


class TestTaskStats:
    """任务统计测试"""

    def test_get_stats(self, client):
        """测试获取队列统计"""
        response = client.get("/api/tasks/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "running" in data
        assert "completed" in data
        assert "failed" in data


class TestTaskRetry:
    """任务重试测试"""

    def test_retry_failed_task(self, client):
        """测试重试失败的任务"""
        # 1. 创建任务
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Retry Test Task", "agent": "dev"}
        )
        task_id = create_resp.json()["task_id"]

        # 2. 将任务标记为失败
        client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "failed", "error": "Original error"}
        )

        # 3. 重试任务
        retry_resp = client.post(f"/api/tasks/{task_id}/retry")
        assert retry_resp.status_code == 200
        data = retry_resp.json()
        assert data["name"] == "Retry Test Task (重试)"
        assert data["status"] == "pending"
        assert data["result"] == {"retry_from": task_id, "original_error": "Original error"}

    def test_retry_non_failed_task(self, client):
        """测试重试非失败状态的任务（应返回400）"""
        # 创建正常任务
        create_resp = client.post(
            "/api/tasks/",
            json={"name": "Pending Task", "agent": "dev"}
        )
        task_id = create_resp.json()["task_id"]

        # 尝试重试（非failed状态）
        retry_resp = client.post(f"/api/tasks/{task_id}/retry")
        assert retry_resp.status_code == 400

    def test_retry_nonexistent_task(self, client):
        """测试重试不存在的任务"""
        response = client.post("/api/tasks/nonexistent_id/retry")
        assert response.status_code == 404
