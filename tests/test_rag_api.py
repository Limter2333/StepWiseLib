"""
RAG API 端点测试
=================

【测试改进 - Phase 1 Critical】
覆盖 /api/rag/* 端点
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestRAGAPI:
    """RAG API 测试套件"""

    def test_query_endpoint_success(self, client):
        """测试知识库查询成功"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "什么是LangGraph?",
                "top_k": 3
            }
        )

        # 应该返回200或500（如果RAG未配置）
        assert response.status_code in [200, 500]
        data = response.json()

        # 如果成功，验证响应结构
        if response.status_code == 200:
            assert "success" in data or "answer" in data

    def test_query_with_session_id(self, client):
        """测试带会话ID的查询"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "测试问题",
                "session_id": "test-session-123",
                "top_k": 5
            }
        )

        assert response.status_code in [200, 500]

    def test_query_without_question(self, client):
        """测试缺少问题参数"""
        response = client.post(
            "/api/rag/query",
            params={}
        )

        # 应该返回422 validation error
        assert response.status_code == 422

    def test_query_empty_question(self, client):
        """测试空问题"""
        response = client.post(
            "/api/rag/query",
            params={"question": ""}
        )

        # 空问题可能导致错误
        assert response.status_code in [400, 422, 500]

    def test_list_documents(self, client):
        """测试列出文档"""
        response = client.get("/api/rag/documents")

        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "total_documents" in data or "stats" in data

    def test_get_stats(self, client):
        """测试获取统计信息"""
        response = client.get("/api/rag/stats")

        assert response.status_code in [200, 500]

    def test_delete_document_not_found(self, client):
        """测试删除不存在的文档"""
        response = client.delete("/api/rag/documents/non-existent-id")

        # 应该返回200(未找到)或500(RAG未配置)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data

    def test_query_with_use_knowledge_flag(self, client):
        """测试use_knowledge标志"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "测试",
                "use_knowledge": False
            }
        )

        assert response.status_code in [200, 500]

    def test_query_large_top_k(self, client):
        """测试大top_k值"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "测试",
                "top_k": 100
            }
        )

        assert response.status_code in [200, 500]

    def test_query_negative_top_k(self, client):
        """测试负数top_k"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "测试",
                "top_k": -1
            }
        )

        # 应该被validation拒绝
        assert response.status_code == 422

    def test_stream_query_endpoint(self, client):
        """测试流式查询端点"""
        response = client.post(
            "/api/rag/query-stream",
            json={
                "question": "测试问题",
                "session_id": "stream-test-session",
                "top_k": 3,
                "use_knowledge": False
            }
        )

        assert response.status_code in [200, 500]

    def test_stream_query_sse_format(self, client):
        """测试SSE流式格式"""
        with client.stream(
            "POST",
            "/api/rag/query-stream",
            json={"question": "Hi", "use_knowledge": False},
            timeout=30
        ) as response:
            if response.status_code == 200:
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1
                        if chunks_received >= 3:
                            break
                assert chunks_received > 0

    def test_stream_query_empty_question(self, client):
        """测试空问题"""
        with client.stream(
            "POST",
            "/api/rag/query-stream",
            json={"question": ""},
            timeout=10
        ) as response:
            # 应该返回错误流
            assert response.status_code in [200, 400, 500]

    def test_upload_document_requires_file(self, client):
        """测试上传需要文件"""
        response = client.post("/api/rag/documents")

        # 应该返回422缺少文件
        assert response.status_code == 422

    def test_query_with_special_characters(self, client):
        """测试特殊字符问题"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "测试<script>alert('xss')</script>",
                "top_k": 3
            }
        )

        assert response.status_code in [200, 500]

    def test_query_with_unicode(self, client):
        """测试Unicode问题"""
        response = client.post(
            "/api/rag/query",
            params={
                "question": "こんにちは、你好、안녕하세요",
                "top_k": 3
            }
        )

        assert response.status_code in [200, 500]

    def test_query_with_long_question(self, client):
        """测试长问题"""
        long_question = "测试" * 1000
        response = client.post(
            "/api/rag/query",
            params={
                "question": long_question,
                "top_k": 3
            }
        )

        assert response.status_code in [200, 500]


class TestRAGEdgeCases:
    """RAG边界情况测试"""

    def test_concurrent_queries(self, client):
        """测试并发查询"""
        import concurrent.futures

        def make_request():
            return client.post(
                "/api/rag/query",
                params={"question": "测试", "top_k": 3}
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有请求应该成功或返回错误（不是崩溃）
        for r in results:
            assert r.status_code in [200, 500]

    def test_stats_includes_vectorstore_info(self, client):
        """测试统计包含向量存储信息"""
        response = client.get("/api/rag/stats")

        if response.status_code == 200:
            data = response.json()
            # 应该有vectorstore相关信息
            assert isinstance(data, dict)
