"""
API使用统计与计费系统 - API Usage Statistics & Billing
====================================================

【功能】
1. API调用统计 - 按端点、会话、用户统计调用量
2. Token消耗追踪 - 记录每个请求的token使用
3. 响应时间分析 - P50/P95/P99延迟统计
4. 成本估算 - 基于token消耗估算费用

【使用场景】
- 监控API使用量和趋势
- 成本控制和预算管理
- 性能优化依据
- 计费和报告
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time


@dataclass
class APIUsageEntry:
    """API使用条目"""
    endpoint: str           # API端点路径
    method: str            # HTTP方法
    timestamp: datetime     # 调用时间
    duration_ms: float     # 响应时间（毫秒）
    token_count: int       # Token消耗
    status_code: int       # 响应状态码
    session_id: Optional[str] = None  # 会话ID
    user_id: Optional[str] = None     # 用户ID
    cost_estimate: float = 0.0           # 费用估算（美元）


@dataclass
class EndpointStats:
    """端点统计"""
    endpoint: str
    method: str
    call_count: int = 0
    total_tokens: int = 0
    total_duration_ms: float = 0.0
    error_count: int = 0
    success_count: int = 0
    last_called: Optional[datetime] = None
    # 延迟百分位
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.call_count if self.call_count > 0 else 0.0

    @property
    def error_rate(self) -> float:
        total = self.error_count + self.success_count
        return self.error_count / total if total > 0 else 0.0

    @property
    def avg_tokens(self) -> float:
        return self.total_tokens / self.call_count if self.call_count > 0 else 0.0


class CostEstimator:
    """成本估算器

    基于实际LLM定价（参考OpenAI GPT-4o）
    - Input: $2.50 / 1M tokens
    - Output: $10.00 / 1M tokens
    """

    INPUT_COST_PER_M = 2.50  # $ per million input tokens
    OUTPUT_COST_PER_M = 10.00  # $ per million output tokens

    @classmethod
    def estimate_cost(cls, input_tokens: int, output_tokens: int) -> float:
        """估算API调用成本"""
        input_cost = (input_tokens / 1_000_000) * cls.INPUT_COST_PER_M
        output_cost = (output_tokens / 1_000_000) * cls.OUTPUT_COST_PER_M
        return input_cost + output_cost

    @classmethod
    def estimate_from_total(cls, total_tokens: int, input_ratio: float = 0.3) -> float:
        """从总token数估算（假设30%输入70%输出）"""
        input_tokens = int(total_tokens * input_ratio)
        output_tokens = total_tokens - input_tokens
        return cls.estimate_cost(input_tokens, output_tokens)


class UsageStats:
    """API使用统计

    【线程安全】使用锁保护并发访问
    """

    def __init__(self, retention_hours: int = 24):
        self._entries: List[APIUsageEntry] = []
        self._lock = threading.RLock()
        self._retention_hours = retention_hours
        self._cleanup_threshold = 1000  # 每1000次清理一次

    def record(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        token_count: int,
        status_code: int,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> float:
        """记录API调用

        Returns:
            费用估算（美元）
        """
        # 成本估算
        cost = CostEstimator.estimate_from_total(token_count)

        entry = APIUsageEntry(
            endpoint=endpoint,
            method=method,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            token_count=token_count,
            status_code=status_code,
            session_id=session_id,
            user_id=user_id,
            cost_estimate=cost
        )

        with self._lock:
            self._entries.append(entry)

            # 定期清理旧数据
            if len(self._entries) > self._cleanup_threshold:
                self._cleanup()

        return cost

    def _cleanup(self):
        """清理过期条目"""
        cutoff = datetime.now() - timedelta(hours=self._retention_hours)
        self._entries = [
            e for e in self._entries
            if e.timestamp > cutoff
        ]

    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, EndpointStats]:
        """获取端点统计"""
        with self._lock:
            stats = defaultdict(lambda: {
                "call_count": 0,
                "total_tokens": 0,
                "total_duration_ms": 0.0,
                "error_count": 0,
                "success_count": 0,
                "last_called": None,
                "durations": []
            })

            for entry in self._entries:
                if endpoint and entry.endpoint != endpoint:
                    continue

                key = f"{entry.method} {entry.endpoint}"
                s = stats[key]
                s["call_count"] += 1
                s["total_tokens"] += entry.token_count
                s["total_duration_ms"] += entry.duration_ms
                s["durations"].append(entry.duration_ms)

                if 200 <= entry.status_code < 300:
                    s["success_count"] += 1
                else:
                    s["error_count"] += 1

                if s["last_called"] is None or entry.timestamp > s["last_called"]:
                    s["last_called"] = entry.timestamp

            # 计算百分位
            result = {}
            for key, s in stats.items():
                durations = sorted(s["durations"])
                n = len(durations)

                result[key] = EndpointStats(
                    endpoint=entry.endpoint,
                    method=entry.method,
                    call_count=s["call_count"],
                    total_tokens=s["total_tokens"],
                    total_duration_ms=s["total_duration_ms"],
                    error_count=s["error_count"],
                    success_count=s["success_count"],
                    last_called=s["last_called"],
                    p50_ms=durations[int(n * 0.5)] if n > 0 else 0.0,
                    p95_ms=durations[int(n * 0.95)] if n > 0 else 0.0,
                    p99_ms=durations[int(n * 0.99)] if n > 0 else 0.0
                )

            return result

    def get_total_stats(self) -> Dict[str, Any]:
        """获取总统计"""
        with self._lock:
            total_calls = len(self._entries)
            total_tokens = sum(e.token_count for e in self._entries)
            total_cost = sum(e.cost_estimate for e in self._entries)
            total_duration = sum(e.duration_ms for e in self._entries)
            error_count = sum(1 for e in self._entries if e.status_code >= 400)

            # 按端点分组
            endpoint_counts = defaultdict(int)
            for e in self._entries:
                endpoint_counts[f"{e.method} {e.endpoint}"] += 1

            # 按小时统计
            hourly_stats = defaultdict(lambda: {"calls": 0, "tokens": 0})
            for e in self._entries:
                hour_key = e.timestamp.strftime("%Y-%m-%d %H:00")
                hourly_stats[hour_key]["calls"] += 1
                hourly_stats[hour_key]["tokens"] += e.token_count

            return {
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 6),
                "avg_duration_ms": total_duration / total_calls if total_calls > 0 else 0.0,
                "error_count": error_count,
                "error_rate": error_count / total_calls if total_calls > 0 else 0.0,
                "unique_endpoints": len(endpoint_counts),
                "top_endpoints": sorted(endpoint_counts.items(), key=lambda x: -x[1])[:10],
                "hourly_stats": dict(sorted(hourly_stats.items())[-24:])  # 最近24小时
            }

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计"""
        with self._lock:
            session_entries = [e for e in self._entries if e.session_id == session_id]

            if not session_entries:
                return {
                    "session_id": session_id,
                    "call_count": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0
                }

            total_tokens = sum(e.token_count for e in session_entries)

            return {
                "session_id": session_id,
                "call_count": len(session_entries),
                "total_tokens": total_tokens,
                "total_cost_usd": round(CostEstimator.estimate_from_total(total_tokens), 6),
                "endpoints_used": list(set(f"{e.method} {e.endpoint}" for e in session_entries))
            }

    def clear(self):
        """清空所有统计"""
        with self._lock:
            self._entries.clear()


# ========== 全局实例 ==========

_usage_stats: Optional[UsageStats] = None


def get_usage_stats() -> UsageStats:
    """获取全局使用统计实例"""
    global _usage_stats
    if _usage_stats is None:
        _usage_stats = UsageStats(retention_hours=24)
    return _usage_stats


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取统计实例
stats = get_usage_stats()

# 2. 记录API调用
cost = stats.record(
    endpoint="/api/rag/query",
    method="POST",
    duration_ms=150.5,
    token_count=500,
    status_code=200,
    session_id="session-123"
)
print(f"Cost: ${cost:.6f}")

# 3. 获取总统计
total = stats.get_total_stats()
print(f"Total calls: {total['total_calls']}")
print(f"Total cost: ${total['total_cost_usd']}")

# 4. 获取端点统计
endpoint_stats = stats.get_endpoint_stats("/api/rag/query")
for name, stat in endpoint_stats.items():
    print(f"{name}: {stat.call_count} calls, {stat.avg_duration_ms:.2f}ms avg")

# 5. 获取会话统计
session = stats.get_session_stats("session-123")
print(f"Session {session['session_id']}: {session['call_count']} calls, ${session['total_cost_usd']}")
"""
