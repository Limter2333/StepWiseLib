"""
MCP独立单元测试
===============
只测试MCP模块本身，不触发其他模块的导入
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMCPStandalone(unittest.TestCase):
    """MCP模块独立测试"""

    def test_mcp_module_structure(self):
        """测试MCP模块结构"""
        from mcp.context_manager import (
            ContextManager,
            ContextSegment,
            ContextWindow,
            ContextPriority,
            CompressionStrategy,
            PriorityCompression,
            SummarizeCompression
        )

        self.assertTrue(hasattr(ContextManager, 'add_context'))
        self.assertTrue(hasattr(ContextManager, 'get_context'))
        self.assertTrue(hasattr(ContextManager, 'get_stats'))
        self.assertTrue(hasattr(ContextManager, 'clear'))

    def test_context_segment(self):
        """测试上下文片段"""
        from mcp.context_manager import ContextSegment, ContextPriority

        seg = ContextSegment(
            id="test_1",
            content="测试内容",
            priority=ContextPriority.HIGH
        )

        self.assertEqual(seg.id, "test_1")
        self.assertEqual(seg.content, "测试内容")
        self.assertEqual(seg.priority, ContextPriority.HIGH)
        self.assertGreater(seg.tokens, 0)

    def test_context_window(self):
        """测试上下文窗口"""
        from mcp.context_manager import ContextWindow, ContextSegment, ContextPriority

        window = ContextWindow(max_tokens=1000)

        self.assertEqual(window.max_tokens, 1000)
        self.assertEqual(window.total_tokens, 0)
        self.assertFalse(window.is_full())

        # 添加片段
        seg = ContextSegment(
            id="test_1",
            content="测试",
            priority=ContextPriority.MEDIUM
        )
        window.add(seg)

        self.assertGreater(window.total_tokens, 0)
        self.assertTrue(window.add(seg))

    def test_context_manager_add(self):
        """测试上下文管理器添加"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        ctx_id = ctx.add_context("测试内容", priority=ContextPriority.HIGH)

        self.assertIsNotNone(ctx_id)
        self.assertEqual(len(ctx.window.segments), 1)
        self.assertGreater(ctx.window.total_tokens, 0)

    def test_context_manager_get_content(self):
        """测试获取上下文内容"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        ctx.add_context("内容1", priority=ContextPriority.HIGH)
        ctx.add_context("内容2", priority=ContextPriority.LOW)

        content = ctx.get_context()
        self.assertIn("内容1", content)
        self.assertIn("内容2", content)

    def test_context_manager_clear(self):
        """测试清空上下文"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        ctx.add_context("内容", priority=ContextPriority.HIGH)

        self.assertGreater(ctx.window.total_tokens, 0)

        ctx.clear()
        self.assertEqual(ctx.window.total_tokens, 0)
        self.assertEqual(len(ctx.window.segments), 0)

    def test_context_manager_stats(self):
        """测试获取统计信息"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        ctx.add_context("测试", priority=ContextPriority.HIGH)
        ctx.add_context("测试2", priority=ContextPriority.LOW)

        stats = ctx.get_stats()

        self.assertIn("current_tokens", stats)
        self.assertIn("max_tokens", stats)
        self.assertIn("utilization", stats)
        self.assertIn("segment_count", stats)
        self.assertEqual(stats["segment_count"], 2)

    def test_context_manager_with_metadata(self):
        """测试带元数据的上下文"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        ctx.add_context(
            "测试内容",
            priority=ContextPriority.HIGH,
            metadata={"source": "test", "user_id": "user_123"}
        )

        segments = ctx.get_context_with_metadata()
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["metadata"]["source"], "test")
        self.assertEqual(segments[0]["metadata"]["user_id"], "user_123")

    def test_priority_compression(self):
        """测试优先级压缩"""
        from mcp.context_manager import (
            ContextManager,
            ContextPriority,
            PriorityCompression
        )

        ctx = ContextManager(max_tokens=100)
        ctx.add_context("低优先级内容" * 10, priority=ContextPriority.LOW)
        ctx.add_context("中优先级内容", priority=ContextPriority.MEDIUM)
        ctx.add_context("高优先级内容", priority=ContextPriority.HIGH)
        ctx.add_context("关键内容", priority=ContextPriority.CRITICAL)

        compressor = PriorityCompression(target_tokens=50)
        compressed = compressor.compress(ctx.window.segments)

        # 压缩后应该保留高优先级内容
        self.assertLessEqual(
            sum(s.tokens for s in compressed),
            50
        )

        # CRITICAL内容应该保留
        critical_segs = [s for s in compressed if s.priority == ContextPriority.CRITICAL]
        self.assertEqual(len(critical_segs), 1)

    def test_summarize_compression(self):
        """测试摘要压缩"""
        from mcp.context_manager import (
            ContextSegment,
            ContextPriority,
            SummarizeCompression
        )

        segs = [
            ContextSegment(id="1", content="这是很长的内容" * 50, priority=ContextPriority.LOW),
            ContextSegment(id="2", content="关键内容", priority=ContextPriority.CRITICAL)
        ]

        compressor = SummarizeCompression()
        compressed = compressor.compress(segs)

        # 压缩后的数量应该不变
        self.assertEqual(len(compressed), 2)

        # 关键内容应该保持原样
        critical = next(s for s in compressed if s.priority == ContextPriority.CRITICAL)
        self.assertEqual(critical.content, "关键内容")


class TestMCPIntegration(unittest.TestCase):
    """MCP集成测试"""

    def test_middleware_import(self):
        """测试中间件导入"""
        from core.mcp_middleware import MCPContextMiddleware

        self.assertTrue(hasattr(MCPContextMiddleware, 'get_context_manager'))
        self.assertTrue(hasattr(MCPContextMiddleware, 'clear_session'))
        self.assertTrue(hasattr(MCPContextMiddleware, 'clear_all'))

    def test_middleware_session_management(self):
        """测试中间件会话管理"""
        from core.mcp_middleware import MCPContextMiddleware

        # 清理测试session
        test_session = "unittest_session"
        MCPContextMiddleware.clear_session(test_session)

        # 应该返回None
        ctx = MCPContextMiddleware.get_context_manager(test_session)
        self.assertIsNone(ctx)


if __name__ == "__main__":
    print("=" * 60)
    print("MCP独立单元测试")
    print("=" * 60)
    print()

    unittest.main(verbosity=2)
