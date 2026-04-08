"""
短期记忆模块 Short-term Memory
==============================

【学习要点】
1. 什么是短期记忆？
   - 会话级记忆
   - 对话上下文
   - 会话结束即清除

2. 短期记忆 vs 长期记忆
   - 短期: 快速访问，容量有限（类似RAM）
   - 长期: 持久化，容量大（类似ROM）
   - Agent需要两者结合才能模拟类人记忆

3. 短期记忆的数据结构
   - 对话历史: messages列表
   - 当前上下文: context dict
   - 会话元数据: session metadata
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import json


class MemoryType(Enum):
    """记忆类型"""
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM_CONTEXT = "system_context"
    TOOL_RESULT = "tool_result"
    INTERMEDIATE_RESULT = "intermediate_result"


class MemoryItem(BaseModel):
    """记忆条目

    【学习要点】Pydantic模型设计
    - type: 记忆类型（便于检索和过滤）
    - content: 记忆内容
    - timestamp: 时间戳（用于LRU淘汰）
    - importance: 重要性评分（0-1）
    - tags: 标签（便于分类）
    """
    type: MemoryType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    importance: float = 0.5  # 0.0 - 1.0
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata
        }


class ConversationSession(BaseModel):
    """对话会话

    【会话管理】
    - 每个用户/线程一个session
    - session包含完整的对话历史
    - session有TTL，过期自动清理
    """
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    memory_items: List[MemoryItem] = []
    context: Dict[str, Any] = {}  # 会话级上下文
    metadata: Dict[str, Any] = {}
    # Token使用量追踪（per-session）
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    request_count: int = 0

    def add_token_usage(self, prompt_tokens: int, completion_tokens: int):
        """记录本会话的token使用量"""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.request_count += 1
        self.last_active = datetime.now()

    def get_token_usage(self) -> Dict:
        """获取本会话的token使用量"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "request_count": self.request_count
        }

    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> MemoryItem:
        """添加记忆条目"""
        item = MemoryItem(
            type=memory_type,
            content=content,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        self.memory_items.append(item)
        self.last_active = datetime.now()
        return item

    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """获取最近的对话消息"""
        messages = []
        for item in self.memory_items[-limit:]:
            if item.type in [MemoryType.USER_MESSAGE, MemoryType.AI_RESPONSE]:
                messages.append(item.to_dict())
        return messages

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        if not self.memory_items:
            return ""

        # 提取最近的上下文
        recent = self.memory_items[-5:]
        summary_parts = []

        for item in recent:
            prefix = "User" if item.type == MemoryType.USER_MESSAGE else "Assistant"
            summary_parts.append(f"{prefix}: {item.content[:100]}...")

        return "\n".join(summary_parts)


class ShortTermMemory:
    """短期记忆管理器

    【架构设计】
    - Session-based: 每个会话独立的记忆空间
    - TTL过期: 自动清理长时间未活跃的会话
    - LRU淘汰: 超出容量时淘汰最旧的记忆
    """

    DEFAULT_TTL_HOURS = 24          # 默认24小时过期
    MAX_ITEMS_PER_SESSION = 1000    # 每个会话最大记忆数
    CLEANUP_INTERVAL_MINUTES = 60   # 清理检查间隔

    def __init__(self, ttl_hours: int = None):
        self.ttl_hours = ttl_hours or self.DEFAULT_TTL_HOURS
        self.sessions: Dict[str, ConversationSession] = {}
        self._last_cleanup = datetime.now()

        # 简单的内存存储
        # 【扩展点】可接入Redis做分布式会话
        # self.redis_client = Redis.from_url("redis://localhost:6379/0")

    def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Dict = None
    ) -> ConversationSession:
        """创建新会话"""
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        self.sessions[session_id] = session
        print(f"[ShortTermMemory] Created session: {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """获取会话"""
        session = self.sessions.get(session_id)

        if session:
            # 更新最后活跃时间
            session.last_active = datetime.now()

            # 检查是否过期
            if self._is_expired(session):
                self.delete_session(session_id)
                return None

        return session

    def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> ConversationSession:
        """获取或创建会话"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id, user_id)
        return session

    def add_to_session(
        self,
        session_id: str,
        content: str,
        memory_type: MemoryType,
        importance: float = 0.5,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> Optional[MemoryItem]:
        """向会话添加记忆"""
        session = self.get_or_create_session(session_id)
        if not session:
            return None

        # LRU淘汰：超出容量时移除最旧的低重要性记忆
        if len(session.memory_items) >= self.MAX_ITEMS_PER_SESSION:
            self._evict_low_importance(session)

        return session.add_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags,
            metadata=metadata
        )

    def search_session(
        self,
        session_id: str,
        query: str,
        limit: int = 5
    ) -> List[MemoryItem]:
        """在会话中搜索记忆（简单关键词匹配）

        【扩展点】可接入向量检索实现语义搜索
        """
        session = self.get_session(session_id)
        if not session:
            return []

        results = []
        query_lower = query.lower()

        for item in reversed(session.memory_items):
            if query_lower in item.content.lower():
                results.append(item)
                if len(results) >= limit:
                    break

        return results

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """获取对话历史"""
        session = self.get_session(session_id)
        if not session:
            return []

        # 返回最近的对话消息
        messages = []
        count = 0
        for item in reversed(session.memory_items):
            if item.type in [MemoryType.USER_MESSAGE, MemoryType.AI_RESPONSE]:
                messages.append(item.to_dict())
                count += 1
                if count >= limit:
                    break

        return list(reversed(messages))

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"[ShortTermMemory] Deleted session: {session_id}")
            return True
        return False

    def _is_expired(self, session: ConversationSession) -> bool:
        """检查会话是否过期"""
        elapsed = datetime.now() - session.last_active
        return elapsed > timedelta(hours=self.ttl_hours)

    def _evict_low_importance(self, session: ConversationSession):
        """淘汰低重要性的记忆"""
        # 找出最老的低重要性记忆
        candidates = [
            (i, item) for i, item in enumerate(session.memory_items)
            if item.importance < 0.3 and
            item.type not in [MemoryType.USER_MESSAGE, MemoryType.AI_RESPONSE]
        ]

        if candidates:
            # 删除最老的一个
            idx, _ = candidates[0]
            session.memory_items.pop(idx)
            print(f"[ShortTermMemory] Evicted low-importance memory")

    def cleanup_expired(self) -> int:
        """清理所有过期会话"""
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if self._is_expired(session)
        ]

        for sid in expired_ids:
            self.delete_session(sid)

        if expired_ids:
            print(f"[ShortTermMemory] Cleaned up {len(expired_ids)} expired sessions")

        return len(expired_ids)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_items = sum(
            len(s.memory_items) for s in self.sessions.values()
        )

        return {
            "active_sessions": len(self.sessions),
            "total_memory_items": total_items,
            "avg_items_per_session": total_items / len(self.sessions) if self.sessions else 0
        }

    def get_session_token_usage(self, session_id: str) -> Optional[Dict]:
        """获取指定会话的token使用量"""
        session = self.get_session(session_id)
        if not session:
            return None
        return {
            "session_id": session_id,
            **session.get_token_usage()
        }


# 全局实例
short_term_memory = ShortTermMemory()
