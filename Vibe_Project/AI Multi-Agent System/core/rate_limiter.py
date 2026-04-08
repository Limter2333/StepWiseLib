"""
API限流与速率控制
================

【功能】
1. 令牌桶算法限流
2. 客户端级别追踪（IP、API Key）
3. 多级限流策略（全局/端点/用户）
4. 限流豁免（白名单）

【使用场景】
- API防滥用保护
- 成本控制（限制LLM调用频率）
- 多租户资源公平分配
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time
import hashlib


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_minute: int = 60      # 每分钟请求数
    requests_per_hour: int = 1000      # 每小时请求数
    burst_size: int = 10               # 突发容量
    enabled: bool = True               # 是否启用


@dataclass
class RateLimitResult:
    """限流结果"""
    allowed: bool
    remaining_requests: int
    reset_in_seconds: float
    limit_type: str  # "minute" or "hour"


class TokenBucket:
    """令牌桶算法

    【原理】
    - 桶以固定速率补充令牌
    - 每个请求消耗一个令牌
    - 桶满时不再补充
    - 无令牌时拒绝请求
    """

    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # 每秒补充令牌数
        self.capacity = capacity  # 桶容量
        self.tokens = float(capacity)
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """尝试消费令牌

        Returns:
            (是否成功, 距离下次令牌可用时间)
        """
        with self.lock:
            now = time.time()
            # 补充令牌
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            else:
                # 计算需要等待多久
                wait_time = (tokens - self.tokens) / self.rate
                return False, wait_time


class SlidingWindowCounter:
    """滑动窗口计数器

    【原理】
    - 将时间划分为固定大小的窗口
    - 统计每个窗口内的请求数
    - 计算滑动窗口内的总数
    """

    def __init__(self, window_size_seconds: int, max_requests: int):
        self.window_size = window_size_seconds
        self.max_requests = max_requests
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """检查是否允许请求

        Returns:
            (是否允许, 剩余请求数)
        """
        with self.lock:
            now = time.time()
            cutoff = now - self.window_size

            # 清理过期记录
            self.requests[key] = [
                t for t in self.requests[key]
                if t > cutoff
            ]

            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                remaining = self.max_requests - len(self.requests[key])
                return True, remaining
            else:
                return False, 0

    def reset(self, key: str):
        """重置计数器"""
        with self.lock:
            if key in self.requests:
                del self.requests[key]


class RateLimiter:
    """API限流器

    【架构】
    - 两级限流：分钟级 + 小时级
    - 令牌桶用于瞬时控制
    - 滑动窗口用于统计
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()

        # 分钟级限流（滑动窗口）
        self.minute_limiter = SlidingWindowCounter(
            window_size_seconds=60,
            max_requests=self.config.requests_per_minute
        )

        # 小时级限流
        self.hourly_limiter = SlidingWindowCounter(
            window_size_seconds=3600,
            max_requests=self.config.requests_per_hour
        )

        # 令牌桶（用于突发控制）
        self.bucket = TokenBucket(
            rate=self.config.requests_per_minute / 60.0,
            capacity=self.config.burst_size
        )

        # 白名单（不进行限流的客户端）
        self.whitelist: set = set()

        # 客户端追踪
        self.client_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_requests": 0,
            "blocked_requests": 0,
            "first_seen": None,
            "last_seen": None
        })
        self.stats_lock = threading.Lock()

    def _get_client_key(self, request) -> str:
        """获取客户端标识

        优先级：X-API-Key > X-Forwarded-For > client.host
        """
        # API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{hashlib.md5(api_key.encode()).hexdigest()[:12]}"

        # IP地址
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _is_whitelisted(self, client_key: str) -> bool:
        """检查是否在白名单"""
        return client_key in self.whitelist

    def check_rate_limit(self, request) -> RateLimitResult:
        """检查是否允许请求

        Args:
            request: FastAPI请求对象

        Returns:
            RateLimitResult
        """
        if not self.config.enabled:
            return RateLimitResult(
                allowed=True,
                remaining_requests=-1,
                reset_in_seconds=0,
                limit_type=""
            )

        client_key = self._get_client_key(request)

        # 白名单直接放行
        if self._is_whitelisted(client_key):
            return RateLimitResult(
                allowed=True,
                remaining_requests=-1,
                reset_in_seconds=0,
                limit_type=""
            )

        # 检查分钟级限流
        minute_allowed, minute_remaining = self.minute_limiter.is_allowed(f"{client_key}:minute")
        if not minute_allowed:
            self._record_blocked(client_key)
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_in_seconds=60,
                limit_type="minute"
            )

        # 检查小时级限流
        hour_allowed, hour_remaining = self.hourly_limiter.is_allowed(f"{client_key}:hour")
        if not hour_allowed:
            self._record_blocked(client_key)
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_in_seconds=3600,
                limit_type="hour"
            )

        # 检查令牌桶
        bucket_allowed, bucket_wait = self.bucket.consume()
        if not bucket_allowed:
            self._record_blocked(client_key)
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_in_seconds=bucket_wait,
                limit_type="burst"
            )

        # 记录成功
        self._record_allowed(client_key)

        return RateLimitResult(
            allowed=True,
            remaining_requests=min(minute_remaining, hour_remaining),
            reset_in_seconds=60,
            limit_type=""
        )

    def _record_allowed(self, client_key: str):
        """记录允许的请求"""
        with self.stats_lock:
            stats = self.client_stats[client_key]
            stats["total_requests"] += 1
            now = datetime.now()
            stats["last_seen"] = now
            if stats["first_seen"] is None:
                stats["first_seen"] = now

    def _record_blocked(self, client_key: str):
        """记录被阻止的请求"""
        with self.stats_lock:
            self.client_stats[client_key]["blocked_requests"] += 1

    def add_to_whitelist(self, client_key: str):
        """添加到白名单"""
        self.whitelist.add(client_key)

    def remove_from_whitelist(self, client_key: str):
        """从白名单移除"""
        self.whitelist.discard(client_key)

    def get_client_stats(self, request) -> Dict:
        """获取客户端统计"""
        client_key = self._get_client_key(request)
        with self.stats_lock:
            return dict(self.client_stats.get(client_key, {}))

    def get_all_stats(self) -> Dict:
        """获取全局统计"""
        with self.stats_lock:
            total_requests = sum(s["total_requests"] for s in self.client_stats.values())
            total_blocked = sum(s["blocked_requests"] for s in self.client_stats.values())
            return {
                "total_clients": len(self.client_stats),
                "total_requests": total_requests,
                "total_blocked": total_blocked,
                "block_rate": total_blocked / total_requests if total_requests > 0 else 0
            }

    def reset_client(self, request):
        """重置客户端限流状态"""
        client_key = self._get_client_key(request)
        self.minute_limiter.reset(f"{client_key}:minute")
        self.hourly_limiter.reset(f"{client_key}:hour")

    def reset_all(self):
        """重置所有限流状态（用于测试）"""
        with self._lock:
            self.clients.clear()
            self.stats = RateLimitStats()


# ========== 全局实例 ==========

_default_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter


def configure_rate_limiter(config: RateLimitConfig):
    """配置全局限流器"""
    global _default_limiter
    _default_limiter = RateLimiter(config)


# ========== FastAPI中间件 ==========

async def rate_limit_middleware(request, call_next):
    """限流中间件

    用法:
        app.middleware("http")(rate_limit_middleware)
    """
    # 延迟导入避免循环依赖
    from starlette.requests import Request
    from fastapi.responses import JSONResponse

    limiter = get_rate_limiter()
    result = limiter.check_rate_limit(request)

    if not result.allowed:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "limit_type": result.limit_type,
                "retry_after": int(result.reset_in_seconds) + 1
            },
            headers={
                "X-RateLimit-Limit": str(limiter.config.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + int(result.reset_in_seconds)),
                "Retry-After": str(int(result.reset_in_seconds) + 1)
            }
        )

    response = await call_next(request)

    # 添加限流响应头
    response.headers["X-RateLimit-Remaining"] = str(result.remaining_requests)
    response.headers["X-RateLimit-Limit"] = str(limiter.config.requests_per_minute)

    return response


# ========== 使用示例 ==========
"""
【基本用法】

from core.rate_limiter import get_rate_limiter, RateLimitConfig

# 配置限流
config = RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10
)
configure_rate_limiter(config)

# 获取限流器
limiter = get_rate_limiter()

# 检查请求
async def some_endpoint(request: Request):
    result = limiter.check_rate_limit(request)
    if not result.allowed:
        raise HTTPException(429, "Rate limit exceeded")
    return {"message": "ok"}

【中间件用法】

app = FastAPI()
app.middleware("http")(rate_limit_middleware)

【白名单】

limiter = get_rate_limiter()
limiter.add_to_whitelist("ip:127.0.0.1")  # 本地不限制
"""


if __name__ == "__main__":
    # 简单测试
    limiter = RateLimiter(RateLimitConfig(
        requests_per_minute=5,
        requests_per_hour=20,
        burst_size=2
    ))

    class MockRequest:
        def __init__(self, ip):
            self.client = type('obj', (object,), {'host': ip})()
            self.headers = {}

    # 模拟请求
    for i in range(10):
        req = MockRequest("192.168.1.1")
        result = limiter.check_rate_limit(req)
        status = "✓" if result.allowed else f"✗ ({result.limit_type})"
        print(f"Request {i+1}: {status}, remaining={result.remaining_requests}")

    # 白名单测试
    limiter.add_to_whitelist("ip:192.168.1.2")
    req = MockRequest("192.168.1.2")
    result = limiter.check_rate_limit(req)
    print(f"Whitelisted request: {'✓' if result.allowed else '✗'}")

    print("\\nRateLimiter OK")
