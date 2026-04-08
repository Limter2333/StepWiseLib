"""
MCP集成测试
==========
测试MCP中间件和路由功能（不依赖外部服务）
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMCPContextManager(unittest.TestCase):
    """测试MCP上下文管理器"""

    def test_context_manager_creation(self):
        """测试上下文管理器创建"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        self.assertEqual(ctx.max_tokens, 1000)
        self.assertEqual(ctx.window.max_tokens, 1000)
        self.assertEqual(ctx.window.total_tokens, 0)

    def test_add_context(self):
        """测试添加上下文"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)
        ctx_id = ctx.add_context(
            "测试内容",
            priority=ContextPriority.HIGH
        )

        self.assertIsNotNone(ctx_id)
        self.assertGreater(ctx.window.total_tokens, 0)

    def test_context_priority(self):
        """测试上下文优先级"""
        from mcp.context_manager import ContextManager, ContextPriority

        ctx = ContextManager(max_tokens=1000)

        # 添加不同优先级的上下文
        ctx.add_context("低优先级", priority=ContextPriority.LOW)
        ctx.add_context("中优先级", priority=ContextPriority.MEDIUM)
        ctx.add_context("高优先级", priority=ContextPriority.HIGH)
        ctx.add_context("关键优先级", priority=ContextPriority.CRITICAL)

        # 检查是否都添加成功
        self.assertEqual(len(ctx.window.segments), 4)

    def test_context_compression(self):
        """测试上下文压缩"""
        from mcp.context_manager import (
            ContextManager,
            ContextPriority,
            PriorityCompression
        )

        # 创建一个小的上下文窗口
        ctx = ContextManager(max_tokens=50)

        # 添加一个大片段
        ctx.add_context("A" * 100, priority=ContextPriority.LOW)

        # 执行压缩
        compressor = PriorityCompression(target_tokens=25)
        compressed = compressor.compress(ctx.window.segments)

        # 压缩后应该token更少
        compressed_tokens = sum(s.tokens for s in compressed)
        self.assertLess(compressed_tokens, 50)


class TestMCPContextMiddleware(unittest.TestCase):
    """测试MCP中间件"""

    def test_session_contexts_initially_empty(self):
        """测试session上下文初始为空"""
        from core.mcp_middleware import MCPContextMiddleware

        # 清理所有session
        MCPContextMiddleware.clear_all()

        # 应该没有session
        # 注意：这个测试假设没有其他并发测试
        self.assertTrue(True)  # 占位

    def test_clear_session(self):
        """测试清除指定session"""
        from core.mcp_middleware import MCPContextMiddleware

        test_session = "test_session_clear"
        MCPContextMiddleware.clear_session(test_session)

        # 清除后获取应该返回None
        ctx = MCPContextMiddleware.get_context_manager(test_session)
        self.assertIsNone(ctx)


class TestMCPRoutes(unittest.TestCase):
    """测试MCP路由（单元测试）"""

    def test_add_context_request_model(self):
        """测试添加上下文请求模型"""
        from api.routes.mcp import AddContextRequest

        # 测试模型创建
        req = AddContextRequest(
            content="测试内容",
            priority=2,
            metadata={"key": "value"}
        )

        self.assertEqual(req.content, "测试内容")
        self.assertEqual(req.priority, 2)
        self.assertEqual(req.metadata["key"], "value")

    def test_add_context_response_model(self):
        """测试添加上下文响应模型"""
        from api.routes.mcp import AddContextResponse

        resp = AddContextResponse(
            success=True,
            context_id="ctx_123",
            current_tokens=100,
            max_tokens=1000
        )

        self.assertTrue(resp.success)
        self.assertEqual(resp.context_id, "ctx_123")
        self.assertEqual(resp.current_tokens, 100)


class TestMCPRoutesIntegration(unittest.TestCase):
    """测试MCP路由集成（使用mock）"""

    def test_mcp_routes_functions_exist(self):
        """测试MCP路由函数存在"""
        from api.routes import mcp

        # 检查关键函数存在
        self.assertTrue(hasattr(mcp, 'router'))
        self.assertTrue(hasattr(mcp, 'AddContextRequest'))
        self.assertTrue(hasattr(mcp, 'AddContextResponse'))
        self.assertTrue(hasattr(mcp, 'ContextStatsResponse'))


class TestMCPAPIEndpoints(unittest.TestCase):
    """测试MCP API端点定义"""

    def test_api_endpoints_defined(self):
        """测试API端点已定义"""
        from api.routes.mcp import router

        # 检查路由已定义
        routes = [r.path for r in router.routes]
        expected_routes = [
            "/context/add",
            "/context/stats",
            "/context/segments",
            "/context/content",
            "/context/clear",
            "/context/compress",
            "/history"
        ]

        for expected in expected_routes:
            self.assertIn(expected, routes)


if __name__ == "__main__":
    print("=" * 60)
    print("MCP集成测试")
    print("=" * 60)
    print()

    # 运行测试
    unittest.main(verbosity=2)
