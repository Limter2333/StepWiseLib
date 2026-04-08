"""
测试RAG多跳推理API

验证用户故事 acceptance criteria
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.rag import router


class TestMultiHopAPI:
    """多跳推理API测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router, prefix="/api/rag")
        return TestClient(app)

    def test_decompose_chain_question(self, client):
        """用户故事: API endpoint /rag/multihop decomposes complex questions"""
        response = client.post("/api/rag/multihop/decompose", params={
            "question": "Alice的工作地天气如何"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sub_questions" in data
        assert isinstance(data["sub_questions"], list)
        assert "reasoning_type" in data

    def test_multihop_query_returns_steps(self, client):
        """用户故事: Multi-hop query returns step-by-step reasoning results"""
        response = client.post("/api/rag/multihop", json={
            "question": "Alice的工作地天气如何",
            "use_knowledge": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["hops"] >= 1
        assert "steps" in data
        assert len(data["steps"]) >= 1
        # Check step structure
        for step in data["steps"]:
            assert "question" in step
            assert "answer" in step

    def test_compare_question_parallel(self, client):
        """用户故事: Compare questions are decomposed into parallel sub-questions"""
        response = client.post("/api/rag/multihop/decompose", params={
            "question": "比较Python和Java的区别"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["reasoning_type"] == "parallel"
        assert len(data["sub_questions"]) >= 2
        # Should mention both Python and Java
        sub_q_text = " ".join(data["sub_questions"])
        assert "Python" in sub_q_text or "python" in sub_q_text.lower()
        assert "Java" in sub_q_text or "java" in sub_q_text.lower()

    def test_aggregate_question_steps(self, client):
        """用户故事: Aggregate questions generate multiple parallel retrieval steps"""
        response = client.post("/api/rag/multihop/decompose", params={
            "question": "这个项目有哪些技术栈和工具"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["step_count"] >= 2

    def test_simple_question_single_hop(self, client):
        """用户故事: Single-hop simple questions return directly without multi-step"""
        response = client.post("/api/rag/multihop", json={
            "question": "什么是Python",
            "use_knowledge": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["hops"] == 1
        assert "final_answer" in data
        assert data["final_answer"] is not None

    def test_multihop_response_structure(self, client):
        """验证多跳响应结构完整"""
        response = client.post("/api/rag/multihop", json={
            "question": "测试问题",
            "use_knowledge": False
        })
        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "success" in data
        assert "original_question" in data
        assert "reasoning_type" in data
        assert "hops" in data
        assert "confidence" in data
        assert "final_answer" in data
        assert "steps" in data

        # Check confidence is a float
        assert isinstance(data["confidence"], float)
        assert 0.0 <= data["confidence"] <= 1.0

    def test_empty_question_rejected(self, client):
        """空问题应被拒绝"""
        response = client.post("/api/rag/multihop", json={
            "question": ""
        })
        assert response.status_code == 400

    def test_decompose_response_structure(self, client):
        """验证分解响应结构"""
        response = client.post("/api/rag/multihop/decompose", params={
            "question": "测试问题"
        })
        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "success" in data
        assert "original_question" in data
        assert "sub_questions" in data
        assert "reasoning_type" in data
        assert "step_count" in data

        # reasoning_type should be a valid value
        valid_types = ["chain", "parallel", "tree"]
        assert data["reasoning_type"] in valid_types
