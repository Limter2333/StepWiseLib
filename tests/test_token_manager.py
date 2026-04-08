"""
测试Token管理器
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.token_manager import TokenManager, TokenStats


class TestTokenManager:
    """TokenManager测试"""

    def setup_method(self):
        """每个测试前重置"""
        self.tm = TokenManager()
        self.tm.reset()  # 从干净状态开始

    def test_initial_state(self):
        """测试初始状态"""
        assert self.tm.stats.total_tokens == 0
        assert self.tm.stats.request_count == 0

    def test_reset(self):
        """测试重置"""
        self.tm.stats.total_tokens = 1000
        self.tm.reset()

        assert self.tm.stats.total_tokens == 0
        assert self.tm.stats.request_count == 0

    def test_consume_success(self):
        """测试成功消费"""
        result = asyncio.run(self.tm.consume(100, 50))

        assert result["success"] is True
        assert self.tm.stats.total_tokens == 150
        assert self.tm.stats.request_count == 1

    def test_consume_accumulates(self):
        """测试消费累加"""
        asyncio.run(self.tm.consume(100, 50))
        asyncio.run(self.tm.consume(200, 100))

        assert self.tm.stats.total_tokens == 450
        assert self.tm.stats.request_count == 2

    def test_get_status(self):
        """测试状态获取"""
        asyncio.run(self.tm.consume(100, 50))
        status = self.tm.get_status()

        assert "current_usage" in status
        assert "prompt_tokens" in status
        assert "completion_tokens" in status
        assert "requests" in status
        assert "last_updated" in status
        assert status["requests"] == 1
        assert status["current_usage"] == 150

    def test_consume_never_blocks(self):
        """测试consume永远不阻塞"""
        # 消费任意数量都不会被阻止
        for i in range(5):
            result = asyncio.run(self.tm.consume(1000 * (i+1), 500 * (i+1)))
            assert result["success"] is True
        assert self.tm.stats.total_tokens > 0  # 确认累加了

    def test_stats_dataclass(self):
        """测试TokenStats数据类"""
        stats = TokenStats(prompt_tokens=100, completion_tokens=50)

        assert stats.prompt_tokens == 100
        assert stats.completion_tokens == 50
        assert stats.total_tokens == 150
        assert stats.request_count == 0


class TestTokenManagerAsync:
    """异步TokenManager测试"""

    def setup_method(self):
        self.tm = TokenManager()
        self.tm.reset()

    def test_async_consume(self):
        """测试异步消费"""
        result = asyncio.run(self.tm.consume(100, 50))
        assert result["success"] is True

    def test_async_multiple_consume(self):
        """测试多次异步消费"""
        async def consume_many():
            for _ in range(10):
                await self.tm.consume(10, 5)

        asyncio.run(consume_many())
        assert self.tm.stats.request_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
