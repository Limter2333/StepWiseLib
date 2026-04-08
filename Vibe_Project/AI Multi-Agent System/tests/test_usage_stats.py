"""
测试API使用统计与计费系统

验证API调用追踪、端点统计、会话统计功能
"""

import pytest
import time
from datetime import datetime


class TestUsageStatsModule:
    """monitoring/usage_stats.py 模块测试"""

    @pytest.fixture
    def stats(self):
        """创建独立的UsageStats实例"""
        import sys
        sys.path.insert(0, 'G:/claude_code_project')
        from monitoring.usage_stats import UsageStats
        return UsageStats(retention_hours=24)

    def test_record_api_call(self, stats):
        """记录API调用并返回成本"""
        cost = stats.record(
            endpoint="/api/chat/completions",
            method="POST",
            duration_ms=150.5,
            token_count=1000,
            status_code=200,
            session_id="test-session-1",
            user_id="user-1"
        )
        assert cost > 0
        assert isinstance(cost, float)

    def test_record_multiple_calls(self, stats):
        """记录多次API调用"""
        for i in range(5):
            stats.record(
                endpoint="/api/rag/query",
                method="POST",
                duration_ms=100.0 + i * 10,
                token_count=500,
                status_code=200,
                session_id="test-session-2"
            )

        total = stats.get_total_stats()
        assert total["total_calls"] == 5
        assert total["total_tokens"] == 2500

    def test_endpoint_stats(self, stats):
        """获取端点统计"""
        stats.record(
            endpoint="/api/chat/completions",
            method="POST",
            duration_ms=100.0,
            token_count=500,
            status_code=200
        )
        stats.record(
            endpoint="/api/chat/completions",
            method="POST",
            duration_ms=200.0,
            token_count=500,
            status_code=200
        )
        stats.record(
            endpoint="/api/rag/query",
            method="POST",
            duration_ms=150.0,
            token_count=300,
            status_code=500
        )

        endpoint_stats = stats.get_endpoint_stats()
        assert "POST /api/chat/completions" in endpoint_stats
        assert "POST /api/rag/query" in endpoint_stats

        chat_stats = endpoint_stats["POST /api/chat/completions"]
        assert chat_stats.call_count == 2
        assert chat_stats.total_tokens == 1000
        assert chat_stats.success_count == 2
        assert chat_stats.error_count == 0

        rag_stats = endpoint_stats["POST /api/rag/query"]
        assert rag_stats.error_count == 1
        assert rag_stats.success_count == 0

    def test_session_stats(self, stats):
        """获取会话统计"""
        session_id = "test-session-stats"
        stats.record(
            endpoint="/api/chat/completions",
            method="POST",
            duration_ms=100.0,
            token_count=500,
            status_code=200,
            session_id=session_id
        )
        stats.record(
            endpoint="/api/rag/query",
            method="POST",
            duration_ms=200.0,
            token_count=300,
            status_code=200,
            session_id=session_id
        )

        session_stats = stats.get_session_stats(session_id)
        assert session_stats["session_id"] == session_id
        assert session_stats["call_count"] == 2
        assert session_stats["total_tokens"] == 800
        assert len(session_stats["endpoints_used"]) == 2

    def test_session_not_found(self, stats):
        """不存在的会话返回空统计"""
        result = stats.get_session_stats("non-existent-session")
        assert result["call_count"] == 0
        assert result["total_tokens"] == 0
        assert result["total_cost_usd"] == 0.0

    def test_total_stats(self, stats):
        """获取总统计"""
        stats.record(
            endpoint="/api/chat/completions",
            method="POST",
            duration_ms=100.0,
            token_count=500,
            status_code=200
        )
        stats.record(
            endpoint="/api/rag/query",
            method="POST",
            duration_ms=200.0,
            token_count=300,
            status_code=400
        )

        total = stats.get_total_stats()
        assert total["total_calls"] == 2
        assert total["total_tokens"] == 800
        assert total["error_count"] == 1
        assert total["unique_endpoints"] == 2
        assert total["error_rate"] == 0.5

    def test_latency_percentiles(self, stats):
        """测试延迟百分位计算"""
        # 记录多个不同延迟的请求
        for i in range(100):
            stats.record(
                endpoint="/api/test/latency",
                method="GET",
                duration_ms=float(100 + i),
                token_count=100,
                status_code=200
            )

        endpoint_stats = stats.get_endpoint_stats()
        test_stats = endpoint_stats["GET /api/test/latency"]

        # P50应该接近150ms
        assert 140 < test_stats.p50_ms < 160
        # P95应该接近195ms
        assert 190 < test_stats.p95_ms < 200
        # P99应该接近199ms
        assert 195 < test_stats.p99_ms < 200

    def test_clear_stats(self, stats):
        """清空统计"""
        stats.record(
            endpoint="/api/test",
            method="GET",
            duration_ms=100.0,
            token_count=100,
            status_code=200
        )

        total = stats.get_total_stats()
        assert total["total_calls"] == 1

        stats.clear()
        total = stats.get_total_stats()
        assert total["total_calls"] == 0

    def test_cost_estimator(self, stats):
        """成本估算器测试"""
        from monitoring.usage_stats import CostEstimator

        # 测试GPT-4o定价: $2.50/1M输入, $10.00/1M输出
        cost = CostEstimator.estimate_cost(input_tokens=1_000_000, output_tokens=1_000_000)
        assert cost == 12.50  # $2.50 + $10.00

        # 测试小量token
        cost = CostEstimator.estimate_cost(input_tokens=1000, output_tokens=500)
        expected = (1000 / 1_000_000) * 2.50 + (500 / 1_000_000) * 10.00
        assert abs(cost - expected) < 0.0001

    def test_estimate_from_total(self, stats):
        """从总token数估算成本（假设30%输入70%输出）"""
        from monitoring.usage_stats import CostEstimator

        cost = CostEstimator.estimate_from_total(total_tokens=1_000_000)
        # 300k输入 + 700k输出
        expected = (300_000 / 1_000_000) * 2.50 + (700_000 / 1_000_000) * 10.00
        assert abs(cost - expected) < 0.0001


class TestCostEstimator:
    """成本估算器独立测试"""

    def test_estimate_cost(self):
        from monitoring.usage_stats import CostEstimator
        cost = CostEstimator.estimate_cost(1_000_000, 1_000_000)
        assert cost == 12.50

    def test_estimate_from_total(self):
        from monitoring.usage_stats import CostEstimator
        cost = CostEstimator.estimate_from_total(1_000_000)
        assert cost == (0.3 * 2.50 + 0.7 * 10.00)
