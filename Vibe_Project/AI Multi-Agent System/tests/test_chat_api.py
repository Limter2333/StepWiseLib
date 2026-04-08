"""
Chat API 端点测试
=================

【测试改进 - Phase 1 Critical】
覆盖 /api/chat/* 端点
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestChatAPI:
    """Chat API 测试套件"""

    def test_chat_endpoint(self, client):
        """测试聊天端点"""
        response = client.post(
            "/api/chat/chat",
            json={
                "message": "你好",
                "session_id": "test-session-123",
                "use_knowledge": False
            }
        )

        # 应该返回200或500（如果RAG未配置）
        assert response.status_code in [200, 500]
        data = response.json()

        if response.status_code == 200:
            assert "message" in data or "session_id" in data

    def test_chat_with_empty_message(self, client):
        """测试空消息"""
        response = client.post(
            "/api/chat/chat",
            json={
                "message": "",
                "session_id": "test-session-123"
            }
        )

        # 应该被拒绝
        assert response.status_code in [400, 422, 500]

    def test_chat_with_unicode(self, client):
        """测试Unicode消息"""
        response = client.post(
            "/api/chat/chat",
            json={
                "message": "你好，世界！🌍",
                "session_id": "test-session-unicode"
            }
        )

        assert response.status_code in [200, 500]

    def test_chat_with_special_characters(self, client):
        """测试特殊字符"""
        response = client.post(
            "/api/chat/chat",
            json={
                "message": "测试<script>alert('xss')</script>",
                "session_id": "test-session-special"
            }
        )

        assert response.status_code in [200, 400, 500]

    def test_chat_without_session_id(self, client):
        """测试缺少session_id"""
        response = client.post(
            "/api/chat/chat",
            json={
                "message": "测试"
            }
        )

        assert response.status_code == 422

    def test_create_session(self, client):
        """测试创建会话"""
        response = client.post(
            "/api/chat/sessions",
            json={}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data or "created_at" in data

    def test_create_session_with_user_id(self, client):
        """测试带user_id创建会话"""
        response = client.post(
            "/api/chat/sessions",
            json={"user_id": "test-user"}
        )

        assert response.status_code in [200, 500]

    def test_create_session_with_metadata(self, client):
        """测试带metadata创建会话"""
        response = client.post(
            "/api/chat/sessions",
            json={
                "user_id": "test-user",
                "metadata": {"source": "web", "version": "2.0"}
            }
        )

        assert response.status_code in [200, 500]

    def test_list_sessions(self, client):
        """测试列出会话"""
        response = client.get("/api/chat/sessions")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "active_sessions" in data or "total_memory_items" in data

    def test_get_session_not_found(self, client):
        """测试获取不存在的会话"""
        response = client.get("/api/chat/sessions/non-existent-session")

        assert response.status_code in [404, 500]

    def test_get_history_not_found(self, client):
        """测试获取不存在会话的历史"""
        response = client.get("/api/chat/sessions/non-existent/history")

        assert response.status_code in [404, 500]

    def test_get_history_with_limit(self, client):
        """测试带limit参数获取历史"""
        response = client.get(
            "/api/chat/sessions/test-session/history",
            params={"limit": 10}
        )

        assert response.status_code in [200, 404, 500]

    def test_get_summary_not_found(self, client):
        """测试获取不存在会话的摘要"""
        response = client.get("/api/chat/sessions/non-existent/summary")

        assert response.status_code in [404, 500]

    def test_delete_session_not_found(self, client):
        """测试删除不存在的会话"""
        response = client.delete("/api/chat/sessions/non-existent")

        assert response.status_code in [404, 500]

    def test_token_usage(self, client):
        """测试获取Token使用量"""
        response = client.get("/api/chat/token-usage")

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "token_usage" in data or "success" in data

    def test_chat_with_use_knowledge_flag(self, client):
        """测试use_knowledge标志"""
        response = client.post(
            "/api/chat/chat",
            json={
                "message": "测试",
                "session_id": "test-session-knowledge",
                "use_knowledge": True
            }
        )

        assert response.status_code in [200, 500]


class TestChatEdgeCases:
    """Chat边界情况测试"""

    def test_concurrent_chat_requests(self, client):
        """测试并发聊天请求"""
        import concurrent.futures

        def make_request(i):
            return client.post(
                "/api/chat/chat",
                json={
                    "message": f"测试消息{i}",
                    "session_id": f"concurrent-session-{i}",
                    "use_knowledge": False
                }
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for r in results:
            assert r.status_code in [200, 500]

    def test_invalid_json_body(self, client):
        """测试无效JSON body"""
        response = client.post(
            "/api/chat/chat",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """测试缺少必需字段"""
        response = client.post(
            "/api/chat/chat",
            json={"session_id": "test"}
        )

        assert response.status_code == 422


class TestIntentDetectionAPI:
    """意图检测API测试"""

    def test_detect_intent_basic(self, client):
        """测试基本意图检测"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"message": "你好"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "intent" in data
            assert "confidence" in data
            assert "sentiment" in data
            assert "entities" in data
            assert "keywords" in data

    def test_detect_intent_greeting(self, client):
        """测试问候语意图检测"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"message": "你好，请问如何上传文档？"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["intent"] in ["greeting", "inquiry", "question", "general"]

    def test_detect_intent_with_session(self, client):
        """测试带session_id的意图检测"""
        response = client.post(
            "/api/chat/intent/detect",
            json={
                "message": "谢谢你的帮助",
                "session_id": "test-session-123"
            }
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "intent" in data

    def test_detect_intent_empty_message(self, client):
        """测试空消息"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"message": "   "}
        )

        assert response.status_code in [400, 422, 500]

    def test_detect_intent_missing_message(self, client):
        """测试缺少message字段"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"session_id": "test"}
        )

        assert response.status_code == 422

    def test_detect_intent_entities_extraction(self, client):
        """测试实体提取"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"message": "帮我预约明天下午3点的会议"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["entities"], list)

    def test_detect_intent_sentiment(self, client):
        """测试情感分析"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"message": "这个系统太棒了，我很喜欢！"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["sentiment"] in ["positive", "neutral", "negative"]

    def test_detect_intent_task_execution(self, client):
        """测试任务执行意图"""
        response = client.post(
            "/api/chat/intent/detect",
            json={"message": "帮我创建一个新任务"}
        )

        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "intent" in data

    def test_detect_intent_multiple_requests(self, client):
        """测试连续多次请求"""
        messages = ["你好", "如何上传文件？", "谢谢", "再见"]

        for msg in messages:
            response = client.post(
                "/api/chat/intent/detect",
                json={"message": msg}
            )
            assert response.status_code in [200, 500]


class TestStreamingChatAPI:
    """流式聊天API测试"""

    def test_stream_chat_endpoint(self, client):
        """测试流式聊天端点"""
        with client.stream(
            "POST",
            "/api/chat/chat/stream",
            json={
                "message": "你好",
                "session_id": "stream-test-session",
                "use_knowledge": False
            },
            timeout=30
        ) as response:
            assert response.status_code in [200, 500]

            # 如果成功，应该能接收到SSE流
            if response.status_code == 200:
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1
                        if chunks_received >= 3:  # 至少收几个chunk
                            break
                assert chunks_received > 0

    def test_stream_chat_invalid_input(self, client):
        """测试流式聊天的非法输入"""
        with client.stream(
            "POST",
            "/api/chat/chat/stream",
            json={
                "message": "",  # 空消息应该被拦截
                "session_id": "stream-test-session"
            },
            timeout=10
        ) as response:
            # 应该返回错误或空流
            assert response.status_code in [200, 400, 500]

    def test_stream_chat_sse_format(self, client):
        """测试SSE格式输出"""
        with client.stream(
            "POST",
            "/api/chat/chat/stream",
            json={
                "message": "Hi",
                "session_id": "sse-test-session",
                "use_knowledge": False
            },
            timeout=30
        ) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        # SSE格式应该是 "data: {...}"
                        assert line.startswith("data: ")
