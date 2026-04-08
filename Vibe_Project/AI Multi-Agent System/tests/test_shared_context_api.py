"""
测试Agent共享上下文API

验证用户故事 acceptance criteria
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.agents import router
from agents.orchestrator.shared_context import get_shared_context, SharedContext, ContextScope


class TestSharedContextAPI:
    """共享上下文API测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/agents")
        return TestClient(app)

    @pytest.fixture
    def clean_ctx(self):
        """每个测试前清空上下文"""
        ctx = get_shared_context()
        ctx.clear(scope=ContextScope.GLOBAL)
        ctx.clear(scope=ContextScope.SESSION, session_id="test-session")
        ctx.clear(scope=ContextScope.TASK, task_id="test-task")
        ctx.clear(scope=ContextScope.AGENT, agent_id="test-agent")
        yield ctx
        # 测试后清理
        ctx.clear(scope=ContextScope.GLOBAL)

    def test_set_and_get_context(self, client, clean_ctx):
        """用户故事: Agent can store value to shared context with TASK scope"""
        # 设置值
        response = client.post("/api/agents/context/set", json={
            "key": "test:value",
            "value": {"test": True},
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 获取值
        response = client.get("/api/agents/context/get", params={
            "key": "test:value",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["value"] == {"test": True}

    def test_cross_agent_context(self, client, clean_ctx):
        """用户故事: Agent can retrieve value stored by another agent"""
        # dev agent 存储值
        response = client.post("/api/agents/context/set", json={
            "key": "generated_code",
            "value": {"code": "def hello(): pass", "language": "python"},
            "scope": "task",
            "agent_id": "dev",
            "task_id": "test-task"
        })
        assert response.status_code == 200

        # test agent 读取 dev agent 的值
        response = client.get("/api/agents/context/get", params={
            "key": "generated_code",
            "scope": "task",
            "agent_id": "dev",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["value"]["code"] == "def hello(): pass"
        assert data["value"]["language"] == "python"

    def test_context_ttl_expiration(self, client, clean_ctx):
        """用户故事: Context values expire after TTL"""
        # 设置1秒过期的值
        response = client.post("/api/agents/context/set", json={
            "key": "temp_value",
            "value": {"temp": True},
            "scope": "task",
            "task_id": "test-task",
            "ttl_seconds": 1
        })
        assert response.status_code == 200

        # 立即获取 - 应该存在
        response = client.get("/api/agents/context/get", params={
            "key": "temp_value",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        assert response.json()["value"] == {"temp": True}

        # 等待2秒让TTL过期
        time.sleep(2)

        # 再次获取 - 应该过期返回None
        response = client.get("/api/agents/context/get", params={
            "key": "temp_value",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        assert response.json()["value"] is None

    def test_context_stats(self, client, clean_ctx):
        """用户故事: Context endpoint returns stats about stored entries"""
        # 添加一些数据
        client.post("/api/agents/context/set", json={
            "key": "global_config",
            "value": {"setting": True},
            "scope": "global"
        })
        client.post("/api/agents/context/set", json={
            "key": "session_data",
            "value": {"session": True},
            "scope": "session",
            "session_id": "test-session"
        })

        # 获取统计
        response = client.get("/api/agents/context/stats")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "global_entries" in data["stats"]
        assert "session_count" in data["stats"]
        assert "task_count" in data["stats"]
        assert "agent_count" in data["stats"]

    def test_context_keys(self, client, clean_ctx):
        """用户故事: Can list all keys in a scope"""
        # 添加多个值
        for i in range(3):
            client.post("/api/agents/context/set", json={
                "key": f"key_{i}",
                "value": {"index": i},
                "scope": "task",
                "task_id": "test-task"
            })

        # 列出所有键
        response = client.get("/api/agents/context/keys", params={
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert len(data["keys"]) >= 3

    def test_context_clear(self, client, clean_ctx):
        """用户故事: Can clear context entries"""
        # 添加值
        client.post("/api/agents/context/set", json={
            "key": "to_clear",
            "value": {"clear": True},
            "scope": "task",
            "task_id": "test-task"
        })

        # 确认存在
        response = client.get("/api/agents/context/get", params={
            "key": "to_clear",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.json()["value"] is not None

        # 清空
        response = client.delete("/api/agents/context/clear", params={
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 确认已删除
        response = client.get("/api/agents/context/get", params={
            "key": "to_clear",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.json()["value"] is None

    def test_context_delete(self, client, clean_ctx):
        """用户故事: Can delete specific context entry"""
        # 添加值
        client.post("/api/agents/context/set", json={
            "key": "to_delete",
            "value": {"delete": True},
            "scope": "task",
            "task_id": "test-task"
        })

        # 删除
        response = client.delete("/api/agents/context/delete", params={
            "key": "to_delete",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200

        # 确认已删除
        response = client.get("/api/agents/context/get", params={
            "key": "to_delete",
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.json()["value"] is None

    def test_context_all(self, client, clean_ctx):
        """用户故事: Can get all key-value pairs in a scope"""
        # 添加多个值
        client.post("/api/agents/context/set", json={
            "key": "item1",
            "value": {"id": 1},
            "scope": "task",
            "task_id": "test-task"
        })
        client.post("/api/agents/context/set", json={
            "key": "item2",
            "value": {"id": 2},
            "scope": "task",
            "task_id": "test-task"
        })

        # 获取所有
        response = client.get("/api/agents/context/all", params={
            "scope": "task",
            "task_id": "test-task"
        })
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], dict)
        assert len(data["data"]) >= 2
