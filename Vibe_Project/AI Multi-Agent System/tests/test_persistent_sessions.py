"""
测试持久会话管理系统

验证会话创建、消息添加、搜索、分支、标注功能
"""

import pytest
import os
import tempfile
from pathlib import Path
from core.persistent_sessions import (
    PersistentSessionStore,
    Message,
    SessionStatus,
    PersistentSession,
    SessionAnnotation
)


@pytest.fixture
def store():
    """创建测试用会话存储"""
    # 使用项目测试数据目录，避免临时文件锁定问题
    db_path = "G:/claude_code_project/data/test_sessions.db"
    # 确保目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    store = PersistentSessionStore(db_path)
    yield store
    # 清理数据但不删除文件
    try:
        conn = store._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM annotations")
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM sessions")
        conn.commit()
    except Exception:
        pass


class TestSessionCreation:
    """会话创建测试"""

    def test_create_session(self, store):
        """创建基本会话"""
        session = store.create_session(user_id="user1", title="Test")
        assert session.session_id is not None
        assert session.user_id == "user1"
        assert session.title == "Test"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.messages) == 0

    def test_create_session_with_messages(self, store):
        """创建带初始消息的会话"""
        messages = [
            Message(role="user", content="Hello", timestamp="2024-01-01T00:00:00"),
            Message(role="assistant", content="Hi!", timestamp="2024-01-01T00:00:01")
        ]
        session = store.create_session(
            user_id="user1",
            title="With Messages",
            initial_messages=messages
        )
        assert len(session.messages) == 2

    def test_create_session_with_parent(self, store):
        """创建有父会话的会话"""
        parent = store.create_session(user_id="user1", title="Parent")
        child = store.create_session(
            user_id="user1",
            title="Child",
            parent_session_id=parent.session_id
        )
        assert child.parent_session_id == parent.session_id


class TestMessageOperations:
    """消息操作测试"""

    def test_add_message(self, store):
        """添加消息"""
        session = store.create_session(user_id="user1")
        store.add_message(session.session_id, "user", "Hello")
        store.add_message(session.session_id, "assistant", "Hi there")

        retrieved = store.get_session(session.session_id)
        assert len(retrieved.messages) == 2
        assert retrieved.messages[0].role == "user"
        assert retrieved.messages[1].role == "assistant"

    def test_add_message_with_metadata(self, store):
        """添加带元数据的消息"""
        session = store.create_session(user_id="user1")
        store.add_message(
            session.session_id,
            "user",
            "Hello",
            metadata={"intent": "greeting"}
        )

        retrieved = store.get_session(session.session_id)
        assert retrieved.messages[0].metadata.get("intent") == "greeting"


class TestSessionRetrieval:
    """会话获取测试"""

    def test_get_existing_session(self, store):
        """获取存在的会话"""
        created = store.create_session(user_id="user1", title="Test")
        retrieved = store.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.session_id == created.session_id

    def test_get_nonexistent_session(self, store):
        """获取不存在的会话"""
        retrieved = store.get_session("nonexistent")
        assert retrieved is None


class TestSessionFork:
    """会话分支测试"""

    def test_fork_session(self, store):
        """Fork会话"""
        original = store.create_session(user_id="user1", title="Original")
        store.add_message(original.session_id, "user", "Message 1")

        fork = store.fork_session(original.session_id, "user1", "Forked")
        assert fork is not None
        assert fork.parent_session_id == original.session_id
        assert fork.title == "Forked"
        assert len(fork.messages) == 1

    def test_fork_nonexistent_returns_none(self, store):
        """Fork不存在的会话返回None"""
        result = store.fork_session("nonexistent", "user1")
        assert result is None


class TestAnnotations:
    """会话标注测试"""

    def test_add_annotation(self, store):
        """添加标注"""
        session = store.create_session(user_id="user1")
        annotation = store.add_annotation(
            session.session_id,
            "user1",
            "This is important!"
        )

        assert annotation is not None
        assert annotation.content == "This is important!"
        assert annotation.session_id == session.session_id

    def test_get_session_with_annotations(self, store):
        """获取带标注的会话"""
        session = store.create_session(user_id="user1")
        store.add_annotation(session.session_id, "user1", "Note 1")
        store.add_annotation(session.session_id, "user1", "Note 2")

        retrieved = store.get_session(session.session_id)
        assert len(retrieved.annotations) == 2


class TestSessionSearch:
    """会话搜索测试"""

    def test_search_by_user(self, store):
        """按用户搜索"""
        store.create_session(user_id="user1", title="Session 1")
        store.create_session(user_id="user2", title="Session 2")
        store.create_session(user_id="user1", title="Session 3")

        results = store.search_sessions(user_id="user1")
        assert len(results) == 2

    def test_search_by_keyword(self, store):
        """按关键词搜索"""
        store.create_session(user_id="user1", title="Project Alpha")
        store.create_session(user_id="user1", title="Project Beta")
        store.create_session(user_id="user1", title="Unrelated")

        results = store.search_sessions(keyword="Project")
        assert len(results) == 2

    def test_search_by_status(self, store):
        """按状态搜索"""
        session = store.create_session(user_id="user1", title="Active")
        store.delete_session(session.session_id, soft=True)

        results = store.search_sessions(status=SessionStatus.DELETED)
        assert len(results) == 1


class TestSessionDeletion:
    """会话删除测试"""

    def test_soft_delete(self, store):
        """软删除"""
        session = store.create_session(user_id="user1")
        store.delete_session(session.session_id, soft=True)

        # 应该还能获取到，但状态是deleted
        retrieved = store.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.status == SessionStatus.DELETED

    def test_hard_delete(self, store):
        """硬删除"""
        session = store.create_session(user_id="user1")
        session_id = session.session_id
        store.delete_session(session_id, soft=False)

        retrieved = store.get_session(session_id)
        assert retrieved is None


class TestSessionStats:
    """会话统计测试"""

    def test_get_stats(self, store):
        """获取统计"""
        store.create_session(user_id="user1", title="S1")
        store.create_session(user_id="user1", title="S2")

        stats = store.get_stats()
        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert "total_messages" in stats
        assert stats["total_sessions"] >= 2
