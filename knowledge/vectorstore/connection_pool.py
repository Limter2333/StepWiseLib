"""
ChromaDB连接池管理器
====================

【功能】
1. 连接池 - 复用连接，减少开销
2. 单例模式 - 全局共享连接
3. 健康检查 - 验证连接可用性
4. 优雅关闭 - 正确释放资源

【使用场景】
- 多线程环境下共享ChromaDB连接
- 避免重复创建连接的开销
- 生产环境资源管理
"""

import threading
import time
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PoolStatus(Enum):
    """连接池状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class PoolConfig:
    """连接池配置"""
    max_size: int = 10              # 最大连接数
    min_size: int = 1                # 最小连接数
    max_lifetime_seconds: float = 3600  # 连接最大生命周期
    checkout_timeout_seconds: float = 30  # 获取连接超时
    health_check_interval_seconds: float = 60  # 健康检查间隔
    enable_stats: bool = True         # 启用统计


@dataclass
class PoolStats:
    """连接池统计"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_checkouts: int = 0
    total_checkins: int = 0
    failed_checkouts: int = 0
    health_checks: int = 0
    unhealthy_checks: int = 0
    last_health_check: Optional[float] = None
    status: PoolStatus = PoolStatus.HEALTHY


class ChromaDBConnection:
    """ChromaDB连接包装器"""

    def __init__(self, conn_id: int, handler: Any, created_at: float):
        self.conn_id = conn_id
        self.handler = handler
        self.created_at = created_at
        self.last_used_at = created_at
        self.checkout_count = 0
        self.isHealthy = True

    def mark_used(self):
        """标记为已使用"""
        self.last_used_at = time.time()
        self.checkout_count += 1

    def age_seconds(self) -> float:
        """连接年龄（秒）"""
        return time.time() - self.created_at

    def idle_seconds(self) -> float:
        """空闲时间（秒）"""
        return time.time() - self.last_used_at


class ChromaDBPool:
    """ChromaDB连接池

    【架构】
    - 预创建min_size个连接
    - 最多创建max_size个连接
    - 连接按需复用
    - 定期健康检查
    """

    _instance: Optional['ChromaDBPool'] = None
    _lock = threading.Lock()

    def __new__(cls, config: Optional[PoolConfig] = None) -> 'ChromaDBPool':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[PoolConfig] = None):
        if self._initialized:
            return

        self.config = config or PoolConfig()
        self._connections: Dict[int, ChromaDBConnection] = {}
        self._available: set = set()  # 可用连接ID
        self._conn_lock = threading.Lock()
        self._next_conn_id = 0
        self._shutdown = False

        # 统计
        self.stats = PoolStats()

        # 初始化连接
        self._initialize_connections()

        # 启动健康检查线程
        self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()

        self._initialized = True
        logger.info(f"ChromaDBPool initialized with {self.config.min_size} connections")

    def _initialize_connections(self):
        """初始化连接"""
        with self._conn_lock:
            for _ in range(self.config.min_size):
                self._create_connection()

    def _create_connection(self) -> Optional[ChromaDBConnection]:
        """创建新连接"""
        if len(self._connections) >= self.config.max_size:
            return None

        try:
            from knowledge.vectorstore.chromadb_handler import ChromaDBHandler
            handler = ChromaDBHandler()
            conn = ChromaDBConnection(
                conn_id=self._next_conn_id,
                handler=handler,
                created_at=time.time()
            )
            self._connections[conn.conn_id] = conn
            self._available.add(conn.conn_id)
            self._next_conn_id += 1
            self.stats.total_connections += 1
            return conn
        except Exception as e:
            logger.error(f"Failed to create ChromaDB connection: {e}")
            return None

    def _get_connection(self) -> Optional[ChromaDBConnection]:
        """获取可用连接"""
        with self._conn_lock:
            # 尝试从可用池获取
            while self._available:
                conn_id = self._available.pop()
                conn = self._connections.get(conn_id)
                if conn and conn.isHealthy:
                    conn.mark_used()
                    self.stats.active_connections += 1
                    self.stats.total_checkouts += 1
                    return conn
                elif conn:
                    # 连接不健康，移除
                    self._connections.pop(conn_id, None)

            # 尝试创建新连接
            if len(self._connections) < self.config.max_size:
                conn = self._create_connection()
                if conn:
                    self.stats.active_connections += 1
                    self.stats.total_checkouts += 1
                    return conn

            # 无可用连接
            self.stats.failed_checkouts += 1
            return None

    def checkout(self, timeout: Optional[float] = None) -> Optional[Any]:
        """检出连接

        Args:
            timeout: 超时时间（秒），None则使用配置的超时

        Returns:
            ChromaDBHandler实例
        """
        if self._shutdown:
            raise RuntimeError("Pool is shutdown")

        timeout = timeout or self.config.checkout_timeout_seconds
        deadline = time.time() + timeout

        while time.time() < deadline:
            conn = self._get_connection()
            if conn:
                return conn.handler

            # 等待一下再重试
            time.sleep(0.1)

        self.stats.failed_checkouts += 1
        raise TimeoutError(f"Failed to checkout ChromaDB connection within {timeout}s")

    def checkin(self, handler: Any):
        """归还连接"""
        with self._conn_lock:
            # 找到对应的连接
            for conn in self._connections.values():
                if conn.handler is handler:
                    if conn.isHealthy:
                        self._available.add(conn.conn_id)
                        self.stats.active_connections -= 1
                        self.stats.total_checkins += 1
                    return

    def _health_check_loop(self):
        """健康检查循环"""
        while not self._shutdown:
            time.sleep(self.config.health_check_interval_seconds)
            if self._shutdown:
                break
            self._perform_health_check()

    def _perform_health_check(self):
        """执行健康检查"""
        self.stats.health_checks += 1

        with self._conn_lock:
            for conn in list(self._connections.values()):
                try:
                    # 简单的健康检查 - 验证handler可用
                    if hasattr(conn.handler, 'vectorstore'):
                        # 执行一个简单的查询验证连接
                        _ = conn.handler.vectorstore._collection.count()
                        conn.isHealthy = True
                    else:
                        conn.isHealthy = False
                except Exception as e:
                    conn.isHealthy = False
                    self.stats.unhealthy_checks += 1
                    logger.warning(f"ChromaDB connection {conn.conn_id} health check failed: {e}")

                    # 从可用池移除不健康的连接
                    self._available.discard(conn.conn_id)

        self.stats.last_health_check = time.time()

        # 更新状态
        unhealthy_ratio = self.stats.unhealthy_checks / max(1, self.stats.health_checks)
        if unhealthy_ratio > 0.5:
            self.stats.status = PoolStatus.UNHEALTHY
        elif unhealthy_ratio > 0.2:
            self.stats.status = PoolStatus.DEGRADED
        else:
            self.stats.status = PoolStatus.HEALTHY

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        with self._conn_lock:
            return {
                "status": self.stats.status.value,
                "total_connections": len(self._connections),
                "active_connections": self.stats.active_connections,
                "idle_connections": len(self._available),
                "max_connections": self.config.max_size,
                "total_checkouts": self.stats.total_checkouts,
                "total_checkins": self.stats.total_checkins,
                "failed_checkouts": self.stats.failed_checkouts,
                "health_checks": self.stats.health_checks,
                "unhealthy_checks": self.stats.unhealthy_checks,
                "last_health_check": self.stats.last_health_check
            }

    def shutdown(self):
        """优雅关闭连接池"""
        self._shutdown = True
        with self._conn_lock:
            self._connections.clear()
            self._available.clear()
        logger.info("ChromaDBPool shutdown complete")

    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        with cls._lock:
            if cls._instance:
                cls._instance.shutdown()
            cls._instance = None


# ========== 上下文管理器 ==========

class ChromaDBConnectionContext:
    """ChromaDB连接上下文管理器

    用法:
        with ChromaDBConnectionContext() as db:
            db.add_documents(...)
    """

    _pool: Optional[ChromaDBPool] = None

    @classmethod
    def _get_pool(cls) -> ChromaDBPool:
        if cls._pool is None:
            cls._pool = ChromaDBPool()
        return cls._pool

    def __enter__(self) -> Any:
        self._handler = self._get_pool().checkout()
        return self._handler

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._get_pool().checkin(self._handler)
        return False


# ========== 便捷函数 ==========

_pool_instance: Optional[ChromaDBPool] = None


def get_chromadb_pool(config: Optional[PoolConfig] = None) -> ChromaDBPool:
    """获取ChromaDB连接池单例"""
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = ChromaDBPool(config)
    return _pool_instance


def get_chromadb() -> Any:
    """获取ChromaDB处理器（从连接池）"""
    pool = get_chromadb_pool()
    return pool.checkout()


def return_chromadb(handler: Any):
    """归还ChromaDB处理器到连接池"""
    pool = get_chromadb_pool()
    pool.checkin(handler)


# ========== 使用示例 ==========
"""
【基本用法】

from knowledge.vectorstore.connection_pool import get_chromadb_pool, ChromaDBConnectionContext

# 获取连接池
pool = get_chromadb_pool()

# 获取统计
stats = pool.get_stats()
print(f"Pool status: {stats['status']}")
print(f"Active connections: {stats['active_connections']}")

# 检出连接
db = pool.checkout(timeout=10)
try:
    # 使用db
    db.add_documents(texts=["hello"], embeddings=[...])
finally:
    # 归还连接
    pool.checkin(db)

【上下文管理器用法】

with ChromaDBConnectionContext() as db:
    db.add_documents(texts=["hello"], embeddings=[...])

【配置连接池】

from knowledge.vectorstore.connection_pool import PoolConfig, get_chromadb_pool

config = PoolConfig(
    max_size=5,
    min_size=2,
    health_check_interval_seconds=30
)
pool = get_chromadb_pool(config)
"""


if __name__ == "__main__":
    print("Testing ChromaDBPool...")

    pool = ChromaDBPool.reset_instance() or ChromaDBPool()

    print(f"Initial stats: {pool.get_stats()}")

    # 检出连接
    db = pool.checkout(timeout=5)
    print(f"After checkout: {pool.get_stats()}")
    print(f"Got handler: {type(db).__name__}")

    # 归还连接
    pool.checkin(db)
    print(f"After checkin: {pool.get_stats()}")

    # 上下文管理器
    with ChromaDBConnectionContext() as db2:
        print(f"In context: {pool.get_stats()}")

    print(f"After context: {pool.get_stats()}")

    print("\nChromaDBPool OK")
