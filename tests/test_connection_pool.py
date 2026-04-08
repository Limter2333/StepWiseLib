"""
测试ChromaDB连接池

验证连接池管理、健康检查、上下文管理器功能
"""

import pytest
import time
from knowledge.vectorstore.connection_pool import (
    ChromaDBPool,
    ChromaDBConnection,
    PoolConfig,
    PoolStatus,
    get_chromadb_pool,
    ChromaDBConnectionContext
)


@pytest.fixture
def pool():
    """创建测试用连接池"""
    config = PoolConfig(max_size=3, min_size=1)
    pool = ChromaDBPool(config)
    yield pool
    pool.shutdown()
    ChromaDBPool.reset_instance()


class TestChromaDBPool:
    """连接池测试"""

    def test_pool_initialization(self, pool):
        """连接池初始化"""
        stats = pool.get_stats()
        assert stats["total_connections"] >= 1
        assert stats["max_connections"] == 3
        assert stats["status"] == "healthy"

    def test_checkout_connection(self, pool):
        """检出连接"""
        db = pool.checkout(timeout=5)
        assert db is not None

        stats = pool.get_stats()
        assert stats["active_connections"] == 1
        assert stats["total_checkouts"] == 1

    def test_checkin_connection(self, pool):
        """归还连接"""
        db = pool.checkout(timeout=5)
        pool.checkin(db)

        stats = pool.get_stats()
        assert stats["active_connections"] == 0
        assert stats["total_checkins"] == 1

    def test_multiple_checkout_checkin(self, pool):
        """多次检出/归还"""
        for i in range(3):
            db = pool.checkout(timeout=5)
            pool.checkin(db)

        stats = pool.get_stats()
        assert stats["total_checkouts"] == 3
        assert stats["total_checkins"] == 3

    def test_context_manager(self, pool):
        """上下文管理器"""
        with ChromaDBConnectionContext() as db:
            stats = pool.get_stats()
            assert stats["active_connections"] == 1

        stats = pool.get_stats()
        assert stats["active_connections"] == 0

    def test_connection_reuse(self, pool):
        """连接复用"""
        db1 = pool.checkout(timeout=5)
        pool.checkin(db1)

        db2 = pool.checkout(timeout=5)
        pool.checkin(db2)

        # 同一个连接应该被复用
        stats = pool.get_stats()
        assert stats["total_connections"] == 1  # 只创建了一个连接

    def test_pool_respects_max_size(self):
        """连接池不超过最大连接数"""
        config = PoolConfig(max_size=2, min_size=2)
        pool = ChromaDBPool(config)

        # 先归还所有初始连接
        initial_conns = []
        for _ in range(2):
            db = pool.checkout(timeout=2)
            initial_conns.append(db)
        for db in initial_conns:
            pool.checkin(db)

        # 现在检出2个连接
        connections = []
        for _ in range(2):
            db = pool.checkout(timeout=2)
            connections.append(db)

        stats = pool.get_stats()
        assert stats["active_connections"] == 2

        # 归还连接
        for db in connections:
            pool.checkin(db)

        pool.shutdown()
        ChromaDBPool.reset_instance()


class TestChromaDBConnection:
    """连接包装器测试"""

    def test_connection_age(self):
        """连接年龄计算"""
        from knowledge.vectorstore.chromadb_handler import ChromaDBHandler

        handler = ChromaDBHandler.__new__(ChromaDBHandler)
        conn = ChromaDBConnection(
            conn_id=1,
            handler=handler,
            created_at=time.time()
        )

        assert conn.age_seconds() < 1
        assert conn.idle_seconds() < 1

    def test_connection_mark_used(self):
        """连接标记使用"""
        from knowledge.vectorstore.chromadb_handler import ChromaDBHandler

        handler = ChromaDBHandler.__new__(ChromaDBHandler)
        conn = ChromaDBConnection(
            conn_id=1,
            handler=handler,
            created_at=time.time()
        )

        assert conn.checkout_count == 0
        conn.mark_used()
        assert conn.checkout_count == 1


class TestPoolConfig:
    """连接池配置测试"""

    def test_default_config(self):
        """默认配置"""
        config = PoolConfig()
        assert config.max_size == 10
        assert config.min_size == 1
        assert config.max_lifetime_seconds == 3600

    def test_custom_config(self):
        """自定义配置"""
        config = PoolConfig(
            max_size=5,
            min_size=2,
            checkout_timeout_seconds=60
        )
        assert config.max_size == 5
        assert config.min_size == 2
        assert config.checkout_timeout_seconds == 60


class TestSingletonFunction:
    """单例函数测试"""

    def test_get_chromadb_pool_singleton(self):
        """获取连接池单例"""
        pool1 = get_chromadb_pool()
        pool2 = get_chromadb_pool()
        assert pool1 is pool2

        pool1.shutdown()
        ChromaDBPool.reset_instance()
