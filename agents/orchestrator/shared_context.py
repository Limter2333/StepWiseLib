"""
Agent共享上下文系统 - Agent Shared Context System
================================================

【功能】
1. 黑板模式 - 所有Agent共享的中央存储
2. 上下文传播 - Agent执行结果可被其他Agent使用
3. 命名空间隔离 - 不同任务/会话的上下文独立
4. TTL自动清理 - 避免无限增长的上下文

【使用场景】
- Dev Agent生成代码后，Test Agent可直接读取
- 多个Agent协作时，中间结果共享
- 跨任务记忆 - Agent可记住之前的决策
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import threading
import json


class ContextScope(Enum):
    """上下文作用域"""
    GLOBAL = "global"      # 全局共享（所有任务可见）
    SESSION = "session"    # 会话级别（同一会话内共享）
    TASK = "task"          # 任务级别（仅当前任务可见）
    AGENT = "agent"        # Agent级别（仅同一Agent私有）


@dataclass
class ContextEntry:
    """上下文条目"""
    key: str
    value: Any
    scope: ContextScope
    agent_id: Optional[str] = None  # 创建此条目的Agent
    task_id: Optional[str] = None    # 关联的任务ID
    session_id: Optional[str] = None # 关联的会话ID
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = 3600  # 默认1小时过期

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)

    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class SharedContext:
    """共享上下文存储器（黑板模式）

    【线程安全】使用读写锁保护并发访问
    """

    def __init__(self):
        self._global_store: Dict[str, ContextEntry] = {}
        self._session_stores: Dict[str, Dict[str, ContextEntry]] = {}
        self._task_stores: Dict[str, Dict[str, ContextEntry]] = {}
        self._agent_stores: Dict[str, Dict[str, ContextEntry]] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 300  # 5分钟清理一次过期条目
        self._last_cleanup = datetime.now()

    def _cleanup_expired(self):
        """清理过期条目"""
        now = datetime.now()
        if (now - self._last_cleanup).total_seconds() < self._cleanup_interval:
            return

        with self._lock:
            # 清理全局存储
            expired_keys = [k for k, v in self._global_store.items() if v.is_expired()]
            for k in expired_keys:
                del self._global_store[k]

            # 清理会话存储
            for session_id in list(self._session_stores.keys()):
                expired = [k for k, v in self._session_stores[session_id].items() if v.is_expired()]
                for k in expired:
                    del self._session_stores[session_id][k]
                if not self._session_stores[session_id]:
                    del self._session_stores[session_id]

            # 清理任务存储
            for task_id in list(self._task_stores.keys()):
                expired = [k for k, v in self._task_stores[task_id].items() if v.is_expired()]
                for k in expired:
                    del self._task_stores[task_id][k]
                if not self._task_stores[task_id]:
                    del self._task_stores[task_id]

            # 清理Agent存储
            for agent_id in list(self._agent_stores.keys()):
                expired = [k for k, v in self._agent_stores[agent_id].items() if v.is_expired()]
                for k in expired:
                    del self._agent_stores[agent_id][k]
                if not self._agent_stores[agent_id]:
                    del self._agent_stores[agent_id]

            self._last_cleanup = now

    def set(
        self,
        key: str,
        value: Any,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = 3600
    ) -> bool:
        """设置上下文值

        Args:
            key: 键名
            value: 值
            scope: 作用域
            agent_id: Agent ID（用于AGENT和追踪）
            task_id: 任务ID（用于TASK和追踪）
            session_id: 会话ID（用于SESSION）
            ttl_seconds: 过期时间（秒），None表示永不过期

        Returns:
            是否设置成功
        """
        self._cleanup_expired()

        entry = ContextEntry(
            key=key,
            value=value,
            scope=scope,
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id,
            ttl_seconds=ttl_seconds
        )

        with self._lock:
            if scope == ContextScope.GLOBAL:
                self._global_store[key] = entry
            elif scope == ContextScope.SESSION:
                if session_id not in self._session_stores:
                    self._session_stores[session_id] = {}
                self._session_stores[session_id][key] = entry
            elif scope == ContextScope.TASK:
                if task_id not in self._task_stores:
                    self._task_stores[task_id] = {}
                self._task_stores[task_id][key] = entry
            elif scope == ContextScope.AGENT:
                if agent_id not in self._agent_stores:
                    self._agent_stores[agent_id] = {}
                self._agent_stores[agent_id][key] = entry

            return True

    def get(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """获取上下文值

        Args:
            key: 键名
            scope: 作用域
            agent_id: Agent ID
            task_id: 任务ID
            session_id: 会话ID
            default: 默认值

        Returns:
            值或默认值
        """
        self._cleanup_expired()

        with self._lock:
            entry = None

            if scope == ContextScope.GLOBAL:
                entry = self._global_store.get(key)
            elif scope == ContextScope.SESSION:
                if session_id in self._session_stores:
                    entry = self._session_stores[session_id].get(key)
            elif scope == ContextScope.TASK:
                if task_id in self._task_stores:
                    entry = self._task_stores[task_id].get(key)
            elif scope == ContextScope.AGENT:
                if agent_id in self._agent_stores:
                    entry = self._agent_stores[agent_id].get(key)

            if entry:
                if entry.is_expired():
                    # 已过期，删除并返回默认值
                    self._delete_entry(key, scope, agent_id, task_id, session_id)
                    return default
                entry.touch()
                return entry.value

            return default

    def _delete_entry(
        self,
        key: str,
        scope: ContextScope,
        agent_id: Optional[str],
        task_id: Optional[str],
        session_id: Optional[str]
    ):
        """删除条目"""
        if scope == ContextScope.GLOBAL:
            self._global_store.pop(key, None)
        elif scope == ContextScope.SESSION and session_id:
            if session_id in self._session_stores:
                self._session_stores[session_id].pop(key, None)
        elif scope == ContextScope.TASK and task_id:
            if task_id in self._task_stores:
                self._task_stores[task_id].pop(key, None)
        elif scope == ContextScope.AGENT and agent_id:
            if agent_id in self._agent_stores:
                self._agent_stores[agent_id].pop(key, None)

    def delete(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """删除上下文值"""
        with self._lock:
            self._delete_entry(key, scope, agent_id, task_id, session_id)
            return True

    def get_all(
        self,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取指定作用域的所有键值对"""
        self._cleanup_expired()

        with self._lock:
            result = {}

            if scope == ContextScope.GLOBAL:
                for k, v in self._global_store.items():
                    if not v.is_expired():
                        result[k] = v.value
            elif scope == ContextScope.SESSION and session_id:
                if session_id in self._session_stores:
                    for k, v in self._session_stores[session_id].items():
                        if not v.is_expired():
                            result[k] = v.value
            elif scope == ContextScope.TASK and task_id:
                if task_id in self._task_stores:
                    for k, v in self._task_stores[task_id].items():
                        if not v.is_expired():
                            result[k] = v.value
            elif scope == ContextScope.AGENT and agent_id:
                if agent_id in self._agent_stores:
                    for k, v in self._agent_stores[agent_id].items():
                        if not v.is_expired():
                            result[k] = v.value

            return result

    def clear(
        self,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> int:
        """清空指定作用域的上下文

        Returns:
            删除的条目数量
        """
        with self._lock:
            count = 0

            if scope == ContextScope.GLOBAL:
                count = len(self._global_store)
                self._global_store.clear()
            elif scope == ContextScope.SESSION and session_id:
                if session_id in self._session_stores:
                    count = len(self._session_stores[session_id])
                    del self._session_stores[session_id]
            elif scope == ContextScope.TASK and task_id:
                if task_id in self._task_stores:
                    count = len(self._task_stores[task_id])
                    del self._task_stores[task_id]
            elif scope == ContextScope.AGENT and agent_id:
                if agent_id in self._agent_stores:
                    count = len(self._agent_stores[agent_id])
                    del self._agent_stores[agent_id]

            return count

    def keys(
        self,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[str]:
        """列出指定作用域的所有键"""
        return list(self.get_all(scope, agent_id, task_id, session_id).keys())

    def exists(
        self,
        key: str,
        scope: ContextScope = ContextScope.GLOBAL,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """检查键是否存在"""
        return self.get(key, scope, agent_id, task_id, session_id, default=...) is not ...

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "global_entries": len(self._global_store),
                "session_count": len(self._session_stores),
                "task_count": len(self._task_stores),
                "agent_count": len(self._agent_stores),
                "total_entries": (
                    len(self._global_store) +
                    sum(len(s) for s in self._session_stores.values()) +
                    sum(len(s) for s in self._task_stores.values()) +
                    sum(len(s) for s in self._agent_stores.values())
                )
            }


# ========== Agent上下文助手 ==========

class AgentContext:
    """Agent上下文助手

    为单个Agent提供便捷的上下文操作接口
    """

    def __init__(
        self,
        agent_id: str,
        shared_context: SharedContext,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.task_id = task_id
        self.session_id = session_id
        self._ctx = shared_context

    def put(self, key: str, value: Any, scope: ContextScope = ContextScope.TASK, ttl_seconds: Optional[int] = 3600):
        """存储值到上下文

        Args:
            key: 键名（建议格式: agent_id:key_name）
            value: 值
            scope: 作用域
            ttl_seconds: 过期时间
        """
        full_key = f"{self.agent_id}:{key}"
        self._ctx.set(
            key=full_key,
            value=value,
            scope=scope,
            agent_id=self.agent_id,
            task_id=self.task_id,
            session_id=self.session_id,
            ttl_seconds=ttl_seconds
        )

    def get(self, key: str, scope: ContextScope = ContextScope.TASK, default: Any = None) -> Any:
        """从上下文获取值"""
        full_key = f"{self.agent_id}:{key}"
        return self._ctx.get(
            key=full_key,
            scope=scope,
            agent_id=self.agent_id,
            task_id=self.task_id,
            session_id=self.session_id,
            default=default
        )

    def read_other(self, agent_id: str, key: str, scope: ContextScope = ContextScope.TASK, default: Any = None) -> Any:
        """读取其他Agent的存储"""
        full_key = f"{agent_id}:{key}"
        return self._ctx.get(
            key=full_key,
            scope=scope,
            agent_id=agent_id,
            task_id=self.task_id,
            session_id=self.session_id,
            default=default
        )

    def list_shared(self, scope: ContextScope = ContextScope.TASK) -> Dict[str, Any]:
        """列出指定作用域的所有共享值"""
        return self._ctx.get_all(
            scope=scope,
            task_id=self.task_id,
            session_id=self.session_id
        )

    def delete(self, key: str, scope: ContextScope = ContextScope.TASK):
        """删除值"""
        full_key = f"{self.agent_id}:{key}"
        self._ctx.delete(
            key=full_key,
            scope=scope,
            agent_id=self.agent_id,
            task_id=self.task_id,
            session_id=self.session_id
        )


# ========== 全局实例 ==========

_shared_context: Optional[SharedContext] = None


def get_shared_context() -> SharedContext:
    """获取全局共享上下文实例"""
    global _shared_context
    if _shared_context is None:
        _shared_context = SharedContext()
    return _shared_context


# ========== API模型 ==========

class ContextSetRequest:
    """设置上下文请求"""
    def __init__(
        self,
        key: str,
        value: Any,
        scope: str = "task",
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = 3600
    ):
        self.key = key
        self.value = value
        self.scope = ContextScope(scope)
        self.agent_id = agent_id
        self.task_id = task_id
        self.session_id = session_id
        self.ttl_seconds = ttl_seconds


class ContextGetRequest:
    """获取上下文请求"""
    def __init__(
        self,
        key: str,
        scope: str = "task",
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.key = key
        self.scope = ContextScope(scope)
        self.agent_id = agent_id
        self.task_id = task_id
        self.session_id = session_id


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取全局共享上下文
ctx = get_shared_context()

# 2. Dev Agent 生成代码后存储到上下文
dev_context = AgentContext(agent_id="dev", shared_context=ctx, task_id="task-123")
dev_context.put("generated_code", {"code": "def hello(): pass", "language": "python"})

# 3. Test Agent 读取 Dev Agent 生成的代码
test_context = AgentContext(agent_id="test", shared_context=ctx, task_id="task-123")
code = test_context.read_other("dev", "generated_code")
print(f"读取到代码: {code}")

# 4. 跨任务记忆 - Agent记住之前的决策
pm_context = AgentContext(agent_id="pm", shared_context=ctx, session_id="session-456")
pm_context.put("architecture_choice", "microservices", scope=ContextScope.SESSION)
later_choice = pm_context.get("architecture_choice", scope=ContextScope.SESSION)

# 5. 全局共享 - 所有Agent可见的配置
ctx.set("llm_provider", "claude", scope=ContextScope.GLOBAL, ttl_seconds=None)

# 6. API调用示例
# POST /api/context/set - 设置值
# GET /api/context/get?key=xxx&scope=task&task_id=xxx - 获取值
# GET /api/context/keys?scope=task&task_id=xxx - 列出所有键
# DELETE /api/context/clear?scope=task&task_id=xxx - 清空上下文
# GET /api/context/stats - 获取统计信息
"""
