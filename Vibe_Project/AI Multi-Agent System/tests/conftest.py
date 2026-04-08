"""
Pytest配置和共享fixtures
========================

【功能】
1. 测试环境配置
2. Rate limiter禁用
3. 共享fixtures
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiter():
    """禁用rate limiter用于测试 - 完全禁用限流"""
    from core.rate_limiter import configure_rate_limiter, RateLimitConfig

    # 配置禁用限流
    config = RateLimitConfig(
        requests_per_minute=999999,
        requests_per_hour=9999999,
        burst_size=999999,
        enabled=False  # 禁用！
    )
    configure_rate_limiter(config)

    yield

    # 测试结束后重置
    from core import rate_limiter
    rate_limiter._default_limiter = None


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """每个测试前后重置rate limiter状态"""
    try:
        from core.rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        if limiter:
            # 确保启用为False
            limiter.config.enabled = False
            # 测试前重置滑动窗口
            limiter.minute_limiter.requests.clear()
            limiter.hourly_limiter.requests.clear()
            limiter.client_stats.clear()
    except Exception:
        pass

    yield

    try:
        from core.rate_limiter import get_rate_limiter
        limiter = get_rate_limiter()
        if limiter:
            # 测试后重置滑动窗口
            limiter.minute_limiter.requests.clear()
            limiter.hourly_limiter.requests.clear()
            limiter.client_stats.clear()
    except Exception:
        pass
