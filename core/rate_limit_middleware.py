"""
限流中间件
==========

FastAPI中间件形式集成全局限流
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

from core.rate_limiter import get_rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI限流中间件

    自动拦截所有请求进行限流检查
    无需在每个端点手动调用
    """

    # 跳过限流的路径
    SKIP_PATHS = {
        "/", "/health", "/health/live", "/health/ready",
        "/docs", "/openapi.json", "/redoc"
    }

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查等路径
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # 跳过favicon
        if request.url.path == "/favicon.ico":
            return await call_next(request)

        limiter = get_rate_limiter()
        result = limiter.check_rate_limit(request)

        if not result.allowed:
            # 记录到审计日志
            try:
                from logs.audit_logger import get_audit_logger, AuditEventType
                audit = get_audit_logger()
                audit.log_rate_limit_exceeded(
                    user_id="anonymous",
                    ip_address=self._get_client_ip(request),
                    limit_type=result.limit_type,
                    endpoint=str(request.url.path)
                )
            except Exception:
                pass  # 审计失败不影响限流

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
# 在 main.py 中注册中间件:

from core.rate_limit_middleware import RateLimitMiddleware

# 在app创建后，路由注册前添加
app.add_middleware(RateLimitMiddleware)

# 限流器会自动应用到所有路由
"""
