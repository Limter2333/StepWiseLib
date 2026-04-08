"""
监控模块测试
============

测试监控指标收集器功能
"""

import sys
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_metrics_collector():
    """测试指标收集器"""
    from monitoring.metrics_collector import (
        MetricsCollector,
        ComponentStatus,
        AgentTracker
    )

    collector = MetricsCollector()

    # 测试系统指标收集
    sys_metrics = collector.collect_system_metrics()
    assert sys_metrics.cpu_percent >= 0
    assert sys_metrics.memory_percent >= 0
    print("    - System metrics collection OK")

    # 测试Agent指标记录
    collector.record_agent_request("dev", 100.5, success=True)
    collector.record_agent_request("dev", 200.0, success=True)
    collector.record_agent_request("dev", 150.0, success=False)

    agent_metrics = collector.get_agent_metrics("dev")
    assert agent_metrics["total_requests"] == 3
    assert agent_metrics["successful_requests"] == 2
    assert agent_metrics["failed_requests"] == 1
    print("    - Agent metrics recording OK")

    # 测试业务指标记录
    collector.record_task(success=True)
    collector.record_task(success=True)
    collector.record_task(success=False)
    collector.record_query()
    collector.update_active_sessions(10)

    business = collector.get_business_metrics()
    assert business["total_tasks"] == 3
    assert business["completed_tasks"] == 2
    assert business["failed_tasks"] == 1
    assert business["active_sessions"] == 10
    print("    - Business metrics recording OK")

    # 测试健康检查
    collector.register_component("api")
    collector.update_component_health("api", ComponentStatus.HEALTHY, 50.0)

    health = collector.get_overall_health()
    assert health["status"] == "healthy"
    assert health["healthy_count"] == 1
    print("    - Health check OK")


def test_agent_tracker():
    """测试Agent追踪器"""
    from monitoring.metrics_collector import AgentTracker, get_metrics_collector

    collector = get_metrics_collector()
    collector.reset()  # 清空之前的数据

    # 使用上下文管理器追踪
    with AgentTracker("test_agent"):
        time.sleep(0.01)  # 模拟执行

    metrics = collector.get_agent_metrics("test_agent")
    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 1
    print("    - AgentTracker context manager OK")


def test_system_metrics_history():
    """测试系统指标历史"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 收集多次系统指标
    for _ in range(5):
        collector.collect_system_metrics()
        time.sleep(0.01)

    # 获取60秒内的指标
    stats = collector.get_system_metrics(duration_seconds=60)
    assert stats["samples"] == 5
    assert stats["cpu_avg"] >= 0
    print("    - System metrics history OK")


def test_agent_leaderboard():
    """测试Agent排行"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录多个Agent的数据
    collector.record_agent_request("dev", 100.0, success=True)
    collector.record_agent_request("dev", 200.0, success=True)
    collector.record_agent_request("doc", 50.0, success=True)
    collector.record_agent_request("test", 300.0, success=False)

    # 按请求数排行
    leaderboard = collector.get_agent_leaderboard(sort_by="total_requests")
    assert leaderboard[0]["agent_name"] == "dev"
    assert leaderboard[0]["total_requests"] == 2
    print("    - Agent leaderboard OK")


def test_full_report():
    """测试完整报告"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 收集一些数据
    collector.collect_system_metrics()
    collector.record_agent_request("dev", 100.0, success=True)
    collector.record_task(success=True)

    # 获取完整报告
    report = collector.get_full_report()

    assert "timestamp" in report
    assert "system" in report
    assert "agents" in report
    assert "business" in report
    assert "health" in report
    print("    - Full report generation OK")


def test_component_health():
    """测试组件健康状态"""
    from monitoring.metrics_collector import MetricsCollector, ComponentStatus

    collector = MetricsCollector()

    # 注册组件
    collector.register_component("api")
    collector.register_component("database")
    collector.register_component("cache")

    # 更新状态
    collector.update_component_health("api", ComponentStatus.HEALTHY, 10.0)
    collector.update_component_health("database", ComponentStatus.HEALTHY, 50.0)
    collector.update_component_health("cache", ComponentStatus.DEGRADED, 200.0)

    health = collector.get_overall_health()
    assert health["status"] == "degraded"  # 因为有DEGRADED组件
    assert health["healthy_count"] == 2
    assert health["degraded_count"] == 1
    print("    - Component health tracking OK")


def test_metrics_reset():
    """测试指标重置"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录一些数据
    collector.record_agent_request("dev", 100.0, success=True)
    collector.record_task(success=True)

    # 重置
    collector.reset()

    # 验证已清空
    agent_metrics = collector.get_agent_metrics("dev")
    assert agent_metrics == {}

    business = collector.get_business_metrics()
    assert business["total_tasks"] == 0
    print("    - Metrics reset OK")


def test_token_metrics():
    """测试Token使用指标"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录Token使用
    collector.record_token_usage("/api/chat", 100, 200)
    collector.record_token_usage("/api/chat", 150, 250)
    collector.record_token_usage("/api/generate", 300, 500)

    # 获取单个端点指标
    chat_tokens = collector.get_token_metrics("/api/chat")
    assert chat_tokens["total_requests"] == 2
    assert chat_tokens["total_input_tokens"] == 250
    assert chat_tokens["total_output_tokens"] == 450
    assert chat_tokens["avg_input_tokens"] == 125.0
    print("    - Token metrics by endpoint OK")

    # 获取所有端点指标
    all_tokens = collector.get_token_metrics()
    assert "/api/chat" in all_tokens
    assert "/api/generate" in all_tokens
    print("    - Token metrics all endpoints OK")

    # 获取总Token使用
    totals = collector.get_total_token_usage()
    assert totals["total_input_tokens"] == 550
    assert totals["total_output_tokens"] == 950
    assert totals["total_tokens"] == 1500
    assert totals["total_requests"] == 3
    print("    - Total token usage OK")


def test_rag_metrics():
    """测试RAG查询指标"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录RAG查询
    collector.record_rag_query("semantic", 50.0, 20.0, 10.0, 5)
    collector.record_rag_query("semantic", 60.0, 25.0, 15.0, 8)
    collector.record_rag_query("hybrid", 80.0, 30.0, 20.0, 10)

    # 获取单个类型指标
    semantic = collector.get_rag_metrics("semantic")
    assert semantic["total_queries"] == 2
    assert semantic["avg_latency_ms"] == 55.0
    assert semantic["avg_results_count"] == 6.5
    print("    - RAG metrics by type OK")

    # 获取所有类型
    all_rag = collector.get_rag_metrics()
    assert "semantic" in all_rag
    assert "hybrid" in all_rag
    print("    - RAG metrics all types OK")

    # 获取RAG总览
    summary = collector.get_rag_summary()
    assert summary["total_queries"] == 3
    assert summary["avg_latency_ms"] == 63.33  # (50+60+80)/3
    print("    - RAG summary OK")


def test_cache_metrics():
    """测试缓存指标"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录缓存命中/未命中
    collector.record_cache_hit("vector_db")
    collector.record_cache_hit("vector_db")
    collector.record_cache_miss("vector_db")
    collector.record_cache_hit("vector_db")
    collector.record_cache_eviction("vector_db")

    # 获取单个缓存指标
    db_cache = collector.get_cache_metrics("vector_db")
    assert db_cache["hits"] == 3
    assert db_cache["misses"] == 1
    assert db_cache["evictions"] == 1
    assert db_cache["hit_rate"] == 0.75
    print("    - Cache metrics by name OK")

    # 获取所有缓存
    all_caches = collector.get_cache_metrics()
    assert "vector_db" in all_caches
    print("    - Cache metrics all caches OK")

    # 获取缓存总览
    summary = collector.get_cache_summary()
    assert summary["total_hits"] == 3
    assert summary["total_misses"] == 1
    assert summary["overall_hit_rate"] == 0.75
    print("    - Cache summary OK")


def test_error_metrics():
    """测试错误指标"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录错误
    collector.record_error("ValidationError", "Invalid input field")
    collector.record_error("ValidationError", "Missing required field")
    collector.record_error("TimeoutError", "Request timeout after 30s")

    # 获取单个错误类型
    validation = collector.get_error_metrics("ValidationError")
    assert validation["count"] == 2
    assert "ValidationError" in validation["error_type"]
    assert validation["last_occurrence"] is not None
    print("    - Error metrics by type OK")

    # 获取所有错误类型
    all_errors = collector.get_error_metrics()
    assert "ValidationError" in all_errors
    assert "TimeoutError" in all_errors
    print("    - Error metrics all types OK")

    # 获取错误总览
    summary = collector.get_error_summary()
    assert summary["total_errors"] == 3
    assert summary["error_types_count"] == 2
    print("    - Error summary OK")


def test_full_report_with_new_metrics():
    """测试完整报告包含新指标"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 收集新指标数据
    collector.record_token_usage("/api/chat", 100, 200)
    collector.record_rag_query("semantic", 50.0, 20.0, 10.0, 5)
    collector.record_cache_hit("vector_db")
    collector.record_error("ValidationError", "Test error")

    # 获取完整报告
    report = collector.get_full_report()

    # 验证新指标字段存在
    assert "tokens" in report
    assert "rag" in report
    assert "cache" in report
    assert "errors" in report

    # 验证tokens结构
    assert "by_endpoint" in report["tokens"]
    assert "totals" in report["tokens"]

    # 验证rag结构
    assert "total_queries" in report["rag"]
    assert "by_type" in report["rag"]

    # 验证cache结构
    assert "total_hits" in report["cache"]
    assert "by_cache" in report["cache"]

    # 验证errors结构
    assert "total_errors" in report["errors"]
    assert "by_type" in report["errors"]

    print("    - Full report with new metrics OK")


def test_metrics_reset_clears_new_metrics():
    """测试重置清空新指标"""
    from monitoring.metrics_collector import MetricsCollector

    collector = MetricsCollector()

    # 记录新指标数据
    collector.record_token_usage("/api/chat", 100, 200)
    collector.record_rag_query("semantic", 50.0, 20.0, 10.0, 5)
    collector.record_cache_hit("vector_db")
    collector.record_error("ValidationError", "Test")

    # 重置
    collector.reset()

    # 验证新指标已清空
    assert collector.get_token_metrics() == {}
    assert collector.get_rag_metrics() == {}
    assert collector.get_cache_metrics() == {}
    assert collector.get_error_metrics() == {}
    print("    - Reset clears new metrics OK")


if __name__ == "__main__":
    print("=" * 60)
    print("Monitoring Module Test")
    print("=" * 60)
    print()

    tests = [
        ("MetricsCollector", test_metrics_collector),
        ("AgentTracker", test_agent_tracker),
        ("SystemMetricsHistory", test_system_metrics_history),
        ("AgentLeaderboard", test_agent_leaderboard),
        ("FullReport", test_full_report),
        ("ComponentHealth", test_component_health),
        ("MetricsReset", test_metrics_reset),
        ("TokenMetrics", test_token_metrics),
        ("RAGMetrics", test_rag_metrics),
        ("CacheMetrics", test_cache_metrics),
        ("ErrorMetrics", test_error_metrics),
        ("FullReportWithNewMetrics", test_full_report_with_new_metrics),
        ("ResetClearsNewMetrics", test_metrics_reset_clears_new_metrics),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"[{name}]")
        try:
            test_func()
            passed += 1
            print("    PASS")
        except AssertionError as e:
            print(f"    FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Result: {passed}/{passed+failed} passed")
    if failed > 0:
        print(f"Failed: {failed}")
    print("=" * 60)
