"""
测试短期记忆模块
"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.short_term import (
    ShortTermMemory, ConversationSession, MemoryItem, MemoryType
)


class TestShortTermMemory:
    """短期记忆测试"""

    def setup_method(self):
        """每个测试前重置"""
        self.memory = ShortTermMemory()
        # 清理现有会话
        for sid in list(self.memory.sessions.keys()):
            self.memory.delete_session(sid)

    def test_create_session(self):
        """测试创建会话"""
        session = self.memory.create_session("test_session_1", user_id="user1")

        assert session is not None
        assert session.session_id == "test_session_1"
        assert session.user_id == "user1"
        assert len(session.memory_items) == 0

    def test_get_session(self):
        """测试获取会话"""
        self.memory.create_session("test_session_1")
        session = self.memory.get_session("test_session_1")

        assert session is not None
        assert session.session_id == "test_session_1"

    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        session = self.memory.get_session("nonexistent")
        assert session is None

    def test_get_or_create_session(self):
        """测试获取或创建会话"""
        # 不存在时创建
        session = self.memory.get_or_create_session("new_session")
        assert session is not None
        assert session.session_id == "new_session"

        # 存在时获取
        session2 = self.memory.get_or_create_session("new_session")
        assert session2.session_id == session.session_id

    def test_add_memory(self):
        """测试添加记忆"""
        session_id = "test_session_1"
        self.memory.create_session(session_id)

        item = self.memory.add_to_session(
            session_id=session_id,
            content="Hello world",
            memory_type=MemoryType.USER_MESSAGE,
            importance=0.8
        )

        assert item is not None
        assert item.content == "Hello world"
        assert item.importance == 0.8

    def test_search_session(self):
        """测试会话内搜索"""
        session_id = "test_session_1"
        self.memory.create_session(session_id)

        self.memory.add_to_session(session_id, "Python is great", MemoryType.USER_MESSAGE)
        self.memory.add_to_session(session_id, "JavaScript is also great", MemoryType.USER_MESSAGE)
        self.memory.add_to_session(session_id, "Hello world", MemoryType.USER_MESSAGE)

        results = self.memory.search_session(session_id, "Python")

        assert len(results) >= 1
        assert "Python" in results[0].content

    def test_conversation_history(self):
        """测试对话历史"""
        session_id = "test_session_1"
        self.memory.create_session(session_id)

        self.memory.add_to_session(
            session_id, "Hello", MemoryType.USER_MESSAGE
        )
        self.memory.add_to_session(
            session_id, "Hi there!", MemoryType.AI_RESPONSE
        )

        history = self.memory.get_conversation_history(session_id)

        assert len(history) == 2

    def test_delete_session(self):
        """测试删除会话"""
        self.memory.create_session("test_session_1")
        result = self.memory.delete_session("test_session_1")

        assert result is True
        assert self.memory.get_session("test_session_1") is None

    def test_session_stats(self):
        """测试统计信息"""
        self.memory.create_session("session1")
        self.memory.create_session("session2")

        self.memory.add_to_session("session1", "test1", MemoryType.USER_MESSAGE)
        self.memory.add_to_session("session1", "test2", MemoryType.USER_MESSAGE)

        stats = self.memory.get_stats()

        assert stats["active_sessions"] == 2
        assert stats["total_memory_items"] == 2


class TestMemoryItem:
    """记忆条目测试"""

    def test_memory_item_creation(self):
        """测试记忆条目创建"""
        item = MemoryItem(
            type=MemoryType.USER_MESSAGE,
            content="Test content",
            importance=0.7,
            tags=["test", "example"]
        )

        assert item.type == MemoryType.USER_MESSAGE
        assert item.content == "Test content"
        assert item.importance == 0.7
        assert "test" in item.tags

    def test_memory_item_to_dict(self):
        """测试转换为字典"""
        item = MemoryItem(
            type=MemoryType.AI_RESPONSE,
            content="Response content"
        )
        d = item.to_dict()

        assert d["type"] == "ai_response"
        assert d["content"] == "Response content"
        assert "timestamp" in d


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
