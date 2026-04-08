"""
持久会话管理系统
===============

【功能】
1. 会话持久化存储 - SQLite数据库
2. 会话搜索 - 按关键词、日期、用户
3. 会话分支 - Fork会话尝试不同路径
4. 会话标注 - 添加评论和标记

【使用场景】
- 跨浏览器/设备继续会话
- 对话历史归档和检索
- QA审计Agent推理过程
- 并行探索不同解决方案
"""

import sqlite3
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import threading


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    FORKED = "forked"
    DELETED = "deleted"


@dataclass
class Message:
    """消息"""
    role: str  # user/assistant/system
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class SessionAnnotation:
    """会话标注"""
    annotation_id: str
    session_id: str
    user_id: str
    content: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersistentSession:
    """持久会话"""
    session_id: str
    user_id: str
    title: str
    status: SessionStatus
    messages: List[Message]
    created_at: str
    updated_at: str
    last_active_at: str
    parent_session_id: Optional[str] = None
    annotations: List[SessionAnnotation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PersistentSessionStore:
    """持久会话存储

    SQLite实现的会话持久化
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = "G:/claude_code_project/data/sessions.db"

        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()

        # 会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT DEFAULT 'Untitled Session',
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_active_at TEXT NOT NULL,
                parent_session_id TEXT,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (parent_session_id) REFERENCES sessions(session_id)
            )
        """)

        # 消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # 标注表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                annotation_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_annotations_session ON annotations(session_id)")

        conn.commit()

    def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        title: str = "Untitled Session",
        parent_session_id: Optional[str] = None,
        initial_messages: Optional[List[Message]] = None
    ) -> PersistentSession:
        """创建新会话"""
        import time
        import random
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(10000, 99999)}"

        now = datetime.now().isoformat()

        session = PersistentSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            status=SessionStatus.ACTIVE,
            messages=initial_messages or [],
            created_at=now,
            updated_at=now,
            last_active_at=now,
            parent_session_id=parent_session_id
        )

        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, title, status, created_at, updated_at, last_active_at, parent_session_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.title,
                session.status.value,
                session.created_at,
                session.updated_at,
                session.last_active_at,
                session.parent_session_id,
                json.dumps(session.metadata)
            ))

            # 插入初始消息
            for msg in session.messages:
                cursor.execute("""
                    INSERT INTO messages (session_id, role, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, msg.role, msg.content, msg.timestamp, json.dumps(msg.metadata)))

            conn.commit()

        return session

    def get_session(self, session_id: str) -> Optional[PersistentSession]:
        """获取会话"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()

            if not row:
                return None

            # 获取消息
            cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp", (session_id,))
            msg_rows = cursor.fetchall()

            # 获取标注
            cursor.execute("SELECT * FROM annotations WHERE session_id = ?", (session_id,))
            ann_rows = cursor.fetchall()

            messages = [Message(
                role=m["role"],
                content=m["content"],
                timestamp=m["timestamp"],
                metadata=json.loads(m["metadata"])
            ) for m in msg_rows]

            annotations = [SessionAnnotation(
                annotation_id=a["annotation_id"],
                session_id=a["session_id"],
                user_id=a["user_id"],
                content=a["content"],
                created_at=a["created_at"],
                metadata=json.loads(a["metadata"])
            ) for a in ann_rows]

            return PersistentSession(
                session_id=row["session_id"],
                user_id=row["user_id"],
                title=row["title"],
                status=SessionStatus(row["status"]),
                messages=messages,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_active_at=row["last_active_at"],
                parent_session_id=row["parent_session_id"],
                annotations=annotations,
                metadata=json.loads(row["metadata"])
            )

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """添加消息到会话"""
        now = datetime.now().isoformat()

        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, now, json.dumps(metadata or {})))

            cursor.execute("""
                UPDATE sessions SET updated_at = ?, last_active_at = ? WHERE session_id = ?
            """, (now, now, session_id))

            conn.commit()
            return True

    def fork_session(self, session_id: str, user_id: str, title: Optional[str] = None) -> Optional[PersistentSession]:
        """Fork会话创建分支"""
        original = self.get_session(session_id)
        if not original:
            return None

        fork_title = title or f"Fork of {original.title}"

        # 生成唯一session_id
        import time
        fork_id = f"fork_{int(time.time() * 1000)}"

        return self.create_session(
            user_id=user_id,
            session_id=fork_id,
            title=fork_title,
            parent_session_id=session_id,
            initial_messages=original.messages.copy()
        )

    def add_annotation(self, session_id: str, user_id: str, content: str) -> Optional[SessionAnnotation]:
        """添加会话标注"""
        import random
        annotation = SessionAnnotation(
            annotation_id=f"ann_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(10000, 99999)}",
            session_id=session_id,
            user_id=user_id,
            content=content,
            created_at=datetime.now().isoformat()
        )

        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO annotations (annotation_id, session_id, user_id, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                annotation.annotation_id,
                annotation.session_id,
                annotation.user_id,
                annotation.content,
                annotation.created_at,
                json.dumps(annotation.metadata)
            ))

            conn.commit()

        return annotation

    def search_sessions(
        self,
        user_id: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        limit: int = 20
    ) -> List[PersistentSession]:
        """搜索会话"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            query = "SELECT * FROM sessions WHERE 1=1"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if keyword:
                query += " AND (title LIKE ? OR session_id LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)

            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            query += " ORDER BY last_active_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                session = self.get_session(row["session_id"])
                if session:
                    results.append(session)

            return results

    def delete_session(self, session_id: str, soft: bool = True) -> bool:
        """删除会话"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            if soft:
                cursor.execute("""
                    UPDATE sessions SET status = ? WHERE session_id = ?
                """, (SessionStatus.DELETED.value, session_id))
            else:
                cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM annotations WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

            conn.commit()
            return True

    def get_user_sessions(
        self,
        user_id: str,
        include_archived: bool = False,
        limit: int = 50
    ) -> List[PersistentSession]:
        """获取用户的所有会话"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            if include_archived:
                cursor.execute("""
                    SELECT session_id FROM sessions
                    WHERE user_id = ?
                    ORDER BY last_active_at DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT session_id FROM sessions
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY last_active_at DESC
                    LIMIT ?
                """, (user_id, limit))

            rows = cursor.fetchall()
            results = []
            for row in rows:
                session = self.get_session(row["session_id"])
                if session:
                    results.append(session)

            return results

    def archive_old_sessions(self, days: int = 30) -> int:
        """归档旧会话"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE sessions
                SET status = ?
                WHERE status = 'active' AND last_active_at < ?
            """, (SessionStatus.ARCHIVED.value, cutoff))

            archived_count = cursor.rowcount
            conn.commit()

            return archived_count

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            total_sessions = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM sessions WHERE status = 'active'")
            active_sessions = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM messages")
            total_messages = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM annotations")
            total_annotations = cursor.fetchone()["count"]

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "total_annotations": total_annotations
            }


# ========== 全局实例 ==========

_session_store: Optional[PersistentSessionStore] = None


def get_session_store() -> PersistentSessionStore:
    """获取会话存储单例"""
    global _session_store
    if _session_store is None:
        _session_store = PersistentSessionStore()
    return _session_store


# ========== 使用示例 ==========
"""
from core.persistent_sessions import PersistentSessionStore, Message, get_session_store

# 获取存储实例
store = get_session_store()

# 创建会话
session = store.create_session(
    user_id="user123",
    title="Project Discussion"
)

# 添加消息
store.add_message(
    session_id=session.session_id,
    role="user",
    content="What is the project status?"
)

store.add_message(
    session_id=session.session_id,
    role="assistant",
    content="The project is 90% complete."
)

# 搜索会话
results = store.search_sessions(
    user_id="user123",
    keyword="project",
    limit=10
)

# Fork会话
fork = store.fork_session(
    session_id=session.session_id,
    user_id="user123",
    title="Alternative Approach"
)

# 添加标注
store.add_annotation(
    session_id=session.session_id,
    user_id="user123",
    content="Important discussion about project scope"
)

# 获取统计
stats = store.get_stats()
"""


if __name__ == "__main__":
    print("Testing PersistentSessionStore...")

    store = PersistentSessionStore("G:/claude_code_project/data/test_sessions.db")

    # 创建会话
    session = store.create_session(
        user_id="test_user",
        title="Test Session"
    )
    print(f"Created session: {session.session_id}")

    # 添加消息
    store.add_message(session.session_id, "user", "Hello, how are you?")
    store.add_message(session.session_id, "assistant", "I'm doing well, thank you!")

    # 获取会话
    retrieved = store.get_session(session.session_id)
    print(f"Session messages: {len(retrieved.messages)}")

    # 搜索
    results = store.search_sessions(user_id="test_user")
    print(f"Found {len(results)} sessions")

    # Fork
    fork = store.fork_session(session.session_id, "test_user", "Forked Session")
    print(f"Forked: {fork.session_id}")

    # 标注
    annotation = store.add_annotation(session.session_id, "test_user", "Important!")
    print(f"Annotation: {annotation.content}")

    # 统计
    stats = store.get_stats()
    print(f"Stats: {stats}")

    print("\nPersistentSessionStore OK")
