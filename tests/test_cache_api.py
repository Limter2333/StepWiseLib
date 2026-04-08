"""
测试RAG查询缓存API

验证用户故事 acceptance criteria
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.rag import router


class TestCacheAPI:
    """RAG查询缓存API测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/rag")
        return TestClient(app)

    @pytest.fixture
    def clean_cache(self):
        """每个测试前清空缓存"""
        from core.response_cache import get_response_cache
        cache = get_response_cache()
        cache.clear()
        yield cache
        cache.clear()

    def test_cache_hit_on_second_call(self, client, clean_cache):
        """用户故事: RAG query returns cached result on second call"""
        question = "测试缓存问题"

        # 第一次调用 - 不命中
        response1 = client.post("/api/rag/query", params={
            "question": question,
            "use_knowledge": False
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"] is True
        assert data1.get("cached") is False

        # 第二次调用 - 应该命中
        response2 = client.post("/api/rag/query", params={
            "question": question,
            "use_knowledge": False
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True
        assert data2.get("cached") is True

        # 验证答案一致
        assert data1["answer"] == data2["answer"]

    def test_cache_stats_endpoint(self, client, clean_cache):
        """用户故事: Cache stats endpoint returns hit/miss statistics"""
        response = client.get("/api/rag/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cache_stats" in data
        stats = data["cache_stats"]
        assert "hits" in stats
        assert "misses" in stats
        assert "sets" in stats
        assert "hit_rate" in stats

    def test_cache_clear(self, client, clean_cache):
        """用户故事: Cache can be cleared via API endpoint"""
        # 添加一些缓存
        client.post("/api/rag/query", params={
            "question": "test question",
            "use_knowledge": False
        })

        # 确认有缓存
        stats_before = client.get("/api/rag/cache/stats").json()
        entries_before = stats_before["cache_stats"]["memory_entries"]

        # 清空
        response = client.delete("/api/rag/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 确认已清空
        stats_after = client.get("/api/rag/cache/stats").json()
        entries_after = stats_after["cache_stats"]["memory_entries"]
        assert entries_after == 0

    def test_use_cache_false_bypasses(self, client, clean_cache):
        """用户故事: Query with use_cache=False bypasses cache"""
        question = "绕过缓存测试"

        # 第一次调用，不使用缓存
        response = client.post("/api/rag/query", params={
            "question": question,
            "use_knowledge": False,
            "use_cache": False
        })
        assert response.status_code == 200
        data = response.json()
        # use_cache=False 应该不会设置缓存
        assert data.get("cached") is not True

        # 如果现在用 use_cache=True 调用同一个问题，应该还是miss（因为上次没缓存）
        response2 = client.post("/api/rag/query", params={
            "question": question,
            "use_knowledge": False,
            "use_cache": True
        })
        data2 = response2.json()
        # 这次应该返回False（第一次设置缓存后第二次才会True）
        assert data2.get("cached") is False

    def test_different_questions_not_cached(self, client, clean_cache):
        """不同问题不会命中同一个缓存"""
        # 问题1
        response1 = client.post("/api/rag/query", params={
            "question": "问题A",
            "use_knowledge": False
        })
        assert response1.status_code == 200

        # 问题2 - 不同问题
        response2 = client.post("/api/rag/query", params={
            "question": "问题B",
            "use_knowledge": False
        })
        assert response2.status_code == 200
        data2 = response2.json()
        # 问题不同，不应该命中
        assert data2.get("cached") is False

    def test_cache_response_structure(self, client, clean_cache):
        """验证缓存响应结构完整"""
        response = client.post("/api/rag/query", params={
            "question": "结构测试",
            "use_knowledge": False
        })
        assert response.status_code == 200
        data = response.json()

        # 验证响应字段
        assert "success" in data
        assert "answer" in data
        assert "sources" in data
        assert "source_count" in data
        assert "cached" in data
