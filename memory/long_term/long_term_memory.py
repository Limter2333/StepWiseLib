"""
长期记忆模块 Long-term Memory
==============================

【学习要点】
1. 什么是长期记忆？
   - 持久化存储
   - 跨会话共享
   - 知识积累

2. 长期记忆的用途
   - 知识库：项目文档、技术方案
   - 经验库：成功/失败案例
   - 偏好库：用户偏好设置
   - 事实库：世界知识

3. 实现方式
   - SQLite: 轻量、零配置、嵌入式
   - ChromaDB: 向量存储、语义检索
   - 组合: SQLite存储元数据 + ChromaDB存储embedding
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import sqlite3
from pathlib import Path
import json


class MemoryCategory(Enum):
    """记忆分类"""
    KNOWLEDGE = "knowledge"           # 知识
    EXPERIENCE = "experience"         # 经验
    PREFERENCE = "preference"         # 偏好
    FACT = "fact"                     # 事实
    RULE = "rule"                     # 规则
    CONTEXT = "context"               # 上下文


class LongTermMemoryItem(BaseModel):
    """长期记忆条目

    【设计要点】
    - category: 分类，便于检索
    - content: 记忆内容
    - embedding: 向量（用于语义搜索）
    - access_count: 访问次数（热点数据）
    - last_accessed: 上次访问时间
    - version: 版本号（支持更新）
    """
    id: Optional[int] = None
    category: MemoryCategory
    content: str
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    access_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    version: int = 1

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "category": self.category.value,
            "content": self.content,
            "summary": self.summary,
            "tags": self.tags,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "version": self.version
        }


class LongTermMemory:
    """长期记忆管理器

    【架构设计】
    - SQLite: 元数据存储、关系查询
    - ChromaDB: 向量存储、语义搜索
    - 组合查询: 先向量检索，再用SQL过滤
    """

    def __init__(
        self,
        db_path: str = "G:/claude_code_project/data/long_term_memory.db",
        vectorstore_enabled: bool = True
    ):
        self.db_path = db_path
        self.vectorstore_enabled = vectorstore_enabled

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化SQLite
        self._init_database()

        # 初始化向量存储（可选）
        if vectorstore_enabled:
            self._init_vectorstore()

    def _init_database(self):
        """初始化SQLite数据库

        【学习要点】SQLite设计
        - 表结构定义
        - 索引优化
        - 事务支持
        """
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # 创建主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                embedding_id TEXT,
                tags TEXT,
                metadata TEXT,
                access_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_accessed TEXT,
                version INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count)
        """)

        self.conn.commit()
        print(f"[LongTermMemory] Database initialized: {self.db_path}")

    def _init_vectorstore(self):
        """初始化向量存储

        【扩展点】
        - ChromaDB: 轻量级
        - Milvus: 生产级
        - FAISS: Facebook的向量搜索库
        """
        try:
            # 延迟导入避免不必要的依赖
            from knowledge.vectorstore.chromadb_handler import ChromaDBHandler

            self.vectorstore = ChromaDBHandler(
                persist_directory="G:/claude_code_project/data/ltm_vectors",
                collection_name="long_term_memory"
            )
            self.vectorstore_enabled = True
            print("[LongTermMemory] Vectorstore enabled")
        except Exception as e:
            print(f"[LongTermMemory] Vectorstore init failed: {e}")
            self.vectorstore_enabled = False

    def add(
        self,
        content: str,
        category: MemoryCategory,
        summary: Optional[str] = None,
        tags: List[str] = None,
        metadata: Dict = None,
        embedding: Optional[List[float]] = None
    ) -> int:
        """添加长期记忆

        Args:
            content: 记忆内容
            category: 分类
            summary: 摘要（可选）
            tags: 标签
            metadata: 额外元数据
            embedding: 向量（用于语义搜索）

        Returns:
            记忆ID
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO memories (
                category, content, summary, tags, metadata,
                created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            category.value,
            content,
            summary or "",
            json.dumps(tags or [], ensure_ascii=False),
            json.dumps(metadata or {}, ensure_ascii=False),
            now,
            now
        ))

        memory_id = cursor.lastrowid
        self.conn.commit()

        # 同时添加到向量存储
        if self.vectorstore_enabled and embedding:
            self._add_to_vector(memory_id, content, embedding)

        print(f"[LongTermMemory] Added memory: {memory_id} [{category.value}]")
        return memory_id

    def get(self, memory_id: int) -> Optional[LongTermMemoryItem]:
        """获取单条记忆"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories WHERE id = ? AND is_active = 1
        """, (memory_id,))

        row = cursor.fetchone()
        if row:
            return self._row_to_item(row)
        return None

    def update(
        self,
        memory_id: int,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """更新记忆"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        updates = []
        params = []

        if content:
            updates.append("content = ?")
            params.append(content)
        if summary:
            updates.append("summary = ?")
            params.append(summary)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags, ensure_ascii=False))
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata, ensure_ascii=False))

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(now)
        updates.append("version = version + 1")
        params.append(memory_id)

        cursor.execute(f"""
            UPDATE memories SET {', '.join(updates)}
            WHERE id = ? AND is_active = 1
        """, params)

        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, memory_id: int, soft: bool = True) -> bool:
        """删除记忆

        Args:
            memory_id: 记忆ID
            soft: True=软删除, False=硬删除
        """
        cursor = self.conn.cursor()

        if soft:
            cursor.execute("""
                UPDATE memories SET is_active = 0 WHERE id = ?
            """, (memory_id,))
        else:
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

        self.conn.commit()
        return cursor.rowcount > 0

    def search(
        self,
        query: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        category: Optional[MemoryCategory] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[LongTermMemoryItem]:
        """搜索记忆

        【多种检索方式】
        1. 关键词搜索: LIKE查询
        2. 语义搜索: 向量相似度
        3. 分类过滤: category
        4. 标签过滤: tags
        """
        results = []

        # 如果有向量，使用向量检索
        if self.vectorstore_enabled and embedding:
            vector_results = self._vector_search(embedding, limit)
            results = [self.get(r["id"]) for r in vector_results if self.get(r["id"])]
        else:
            # 使用SQL检索
            results = self._sql_search(
                query=query,
                category=category,
                tags=tags,
                limit=limit
            )

        return [r for r in results if r]

    def _sql_search(
        self,
        query: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[LongTermMemoryItem]:
        """SQL方式搜索"""
        cursor = self.conn.cursor()

        sql = "SELECT * FROM memories WHERE is_active = 1"
        params = []

        if query:
            sql += " AND (content LIKE ? OR summary LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        if category:
            sql += " AND category = ?"
            params.append(category.value)

        if tags:
            for tag in tags:
                sql += " AND tags LIKE ?"
                params.append(f"%{tag}%")

        sql += " ORDER BY access_count DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return [self._row_to_item(row) for row in rows]

    def _vector_search(
        self,
        embedding: List[float],
        limit: int = 10
    ) -> List[Dict]:
        """向量方式搜索"""
        if not self.vectorstore_enabled:
            return []

        results = self.vectorstore.similarity_search_by_vector(embedding, k=limit)
        return results

    def _add_to_vector(
        self,
        memory_id: int,
        content: str,
        embedding: List[float]
    ):
        """添加到向量存储"""
        if not self.vectorstore_enabled:
            return

        # 注意：这里需要实现向量存储的add方法
        # 简化实现省略

    def _row_to_item(self, row: sqlite3.Row) -> LongTermMemoryItem:
        """将数据库行转换为对象"""
        return LongTermMemoryItem(
            id=row["id"],
            category=MemoryCategory(row["category"]),
            content=row["content"],
            summary=row["summary"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            access_count=row["access_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]) if row["last_accessed"] else None,
            version=row["version"]
        )

    def increment_access(self, memory_id: int):
        """增加访问计数"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE memories
            SET access_count = access_count + 1,
                last_accessed = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), memory_id))
        self.conn.commit()

    def get_by_category(
        self,
        category: MemoryCategory,
        limit: int = 50
    ) -> List[LongTermMemoryItem]:
        """按分类获取记忆"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM memories
            WHERE category = ? AND is_active = 1
            ORDER BY updated_at DESC
            LIMIT ?
        """, (category.value, limit))

        rows = cursor.fetchall()
        return [self._row_to_item(row) for row in rows]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as total FROM memories WHERE is_active = 1
        """)
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM memories WHERE is_active = 1
            GROUP BY category
        """)
        by_category = {row["category"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT SUM(access_count) as total_access FROM memories
        """)
        total_access = cursor.fetchone()["total_access"] or 0

        return {
            "total_memories": total,
            "by_category": by_category,
            "total_accesses": total_access,
            "vectorstore_enabled": self.vectorstore_enabled
        }

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()
            print("[LongTermMemory] Database connection closed")


# 全局实例
long_term_memory = LongTermMemory()
