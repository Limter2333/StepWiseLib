"""
API响应缓存层 - API Response Cache
=================================

【功能】
1. LLM响应缓存 - 相同问题直接返回缓存，避免重复LLM调用
2. 多级缓存 - 内存缓存 + 持久化缓存
3. 自动过期 - TTL机制确保数据新鲜
4. 缓存统计 - 命中率、存储量监控

【使用场景】
- 知识库查询 - 相同问题直接返回缓存
- RAG查询 - 减少重复向量检索
- Agent任务 - 缓存Agent执行结果
"""

from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import threading
import time
import os


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600  # 默认1小时
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds <= 0:
            return False
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds

    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class ResponseCache:
    """API响应缓存

    【线程安全】使用读写锁保护并发访问
    【多级存储】内存 + 持久化
    """

    def __init__(
        self,
        cache_dir: str = "data/cache",
        max_memory_entries: int = 1000,
        default_ttl: int = 3600,
        enable_persistence: bool = True
    ):
        self._memory_store: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._cache_dir = cache_dir
        self._max_entries = max_memory_entries
        self._default_ttl = default_ttl
        self._enable_persistence = enable_persistence
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }

        # 确保缓存目录存在
        if self._enable_persistence:
            os.makedirs(cache_dir, exist_ok=True)

        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 创建规范化的数据字符串
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, ensure_ascii=False)
        hash_value = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_value}"

    def _cleanup_loop(self):
        """定期清理过期条目"""
        while True:
            time.sleep(60)  # 每分钟检查一次
            self._cleanup_expired()

    def _cleanup_expired(self):
        """清理过期条目"""
        with self._lock:
            expired_keys = [
                k for k, v in self._memory_store.items()
                if v.is_expired()
            ]
            for k in expired_keys:
                del self._memory_store[k]
                self._stats["evictions"] += 1

            # 如果超过最大条目数，删除最久未使用的
            while len(self._memory_store) > self._max_entries:
                oldest_key = min(
                    self._memory_store.keys(),
                    key=lambda k: self._memory_store[k].last_accessed
                )
                del self._memory_store[oldest_key]
                self._stats["evictions"] += 1

    def get(self, key: str) -> Tuple[Optional[Any], bool]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            (值, 是否命中)
        """
        with self._lock:
            if key not in self._memory_store:
                self._stats["misses"] += 1
                return None, False

            entry = self._memory_store[key]

            # 检查过期
            if entry.is_expired():
                del self._memory_store[key]
                self._stats["misses"] += 1
                return None, False

            # 更新访问统计
            entry.touch()
            self._stats["hits"] += 1

            # 尝试从持久化存储加载（如果内存中的是旧数据）
            if self._enable_persistence:
                persisted = self._load_from_disk(key)
                if persisted and not entry.is_expired():
                    return persisted.value, True

            return entry.value, True

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 过期时间（秒）
            metadata: 元数据

        Returns:
            是否设置成功
        """
        if ttl_seconds is None:
            ttl_seconds = self._default_ttl

        with self._lock:
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl_seconds,
                metadata=metadata or {}
            )

            self._memory_store[key] = entry
            self._stats["sets"] += 1

            # 持久化
            if self._enable_persistence:
                self._save_to_disk(entry)

            return True

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._memory_store:
                del self._memory_store[key]
                self._remove_from_disk(key)
                return True
            return False

    def clear(self, prefix: Optional[str] = None) -> int:
        """清空缓存

        Args:
            prefix: 可选的前缀，只清空匹配的键

        Returns:
            删除的条目数
        """
        with self._lock:
            if prefix is None:
                count = len(self._memory_store)
                self._memory_store.clear()
                if self._enable_persistence:
                    self._clear_disk()
                return count

            # 只删除匹配前缀的
            keys_to_delete = [k for k in self._memory_store.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._memory_store[k]
                self._remove_from_disk(k)
            return len(keys_to_delete)

    def exists(self, key: str) -> bool:
        """检查键是否存在（未过期）"""
        value, hit = self.get(key)
        return hit

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0.0

            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "evictions": self._stats["evictions"],
                "hit_rate": round(hit_rate * 100, 2),
                "memory_entries": len(self._memory_store),
                "max_entries": self._max_entries
            }

    # ========== 持久化操作 ==========

    def _get_disk_path(self, key: str) -> str:
        """获取磁盘存储路径"""
        # 使用键的哈希值作为文件名，避免特殊字符问题
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self._cache_dir, f"{safe_key}.json")

    def _save_to_disk(self, entry: CacheEntry):
        """保存到磁盘"""
        try:
            path = self._get_disk_path(entry.key)
            data = {
                "key": entry.key,
                "value": entry.value,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "ttl_seconds": entry.ttl_seconds,
                "metadata": entry.metadata
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 静默处理持久化失败

    def _load_from_disk(self, key: str) -> Optional[CacheEntry]:
        """从磁盘加载"""
        try:
            path = self._get_disk_path(key)
            if not os.path.exists(path):
                return None

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entry = CacheEntry(
                key=data["key"],
                value=data["value"],
                created_at=datetime.fromisoformat(data["created_at"]),
                last_accessed=datetime.fromisoformat(data["last_accessed"]),
                access_count=data.get("access_count", 0),
                ttl_seconds=data.get("ttl_seconds", 3600),
                metadata=data.get("metadata", {})
            )

            # 检查是否过期
            if entry.is_expired():
                self._remove_from_disk(key)
                return None

            return entry
        except Exception:
            return None

    def _remove_from_disk(self, key: str):
        """从磁盘删除"""
        try:
            path = self._get_disk_path(key)
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def _clear_disk(self):
        """清空磁盘缓存"""
        try:
            for f in os.listdir(self._cache_dir):
                if f.endswith('.json'):
                    os.remove(os.path.join(self._cache_dir, f))
        except Exception:
            pass


# ========== 便捷装饰器 ==========

def cached(
    cache: ResponseCache,
    prefix: str = "default",
    ttl_seconds: Optional[int] = None,
    key_builder: Optional[callable] = None
):
    """缓存装饰器

    Args:
        cache: ResponseCache实例
        prefix: 缓存键前缀
        ttl_seconds: 过期时间
        key_builder: 自定义键构建函数

    Usage:
        cache = ResponseCache()

        @cached(cache, prefix="user", ttl_seconds=3600)
        async def get_user(user_id: str):
            return await db.get_user(user_id)
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # 构建缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)

            # 尝试获取缓存
            cached_value, hit = cache.get(cache_key)
            if hit:
                return cached_value

            # 执行函数
            result = await func(*args, **kwargs)

            # 存储结果
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)

            return result

        def sync_wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)

            cached_value, hit = cache.get(cache_key)
            if hit:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)

            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ========== 全局实例 ==========

_response_cache: Optional[ResponseCache] = None


def get_response_cache() -> ResponseCache:
    """获取全局响应缓存实例"""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache(
            cache_dir="data/cache",
            max_memory_entries=1000,
            default_ttl=3600,
            enable_persistence=True
        )
    return _response_cache


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取缓存实例
cache = get_response_cache()

# 2. 手动缓存
cache.set("user:123", {"name": "Alice", "age": 30}, ttl_seconds=3600)
value, hit = cache.get("user:123")
print(f"Cache hit: {hit}, Value: {value}")

# 3. 使用装饰器
@cached(cache, prefix="query", ttl_seconds=1800)
async def query_knowledge(question: str):
    return await rag_pipeline.query(question)

# 4. 监控统计
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Memory entries: {stats['memory_entries']}")

# 5. 清空缓存
cache.clear(prefix="query")
"""
