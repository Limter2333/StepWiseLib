"""
监控指标模块 - Monitoring Metrics
================================

【功能】
1. 系统指标收集 - CPU、内存、响应时间
2. Agent性能追踪 - 各Agent执行次数、成功率、延迟
3. 业务指标 - 任务完成数、用户活跃度
4. 健康检查 - 系统各组件状态

【使用场景】
- 实时监控dashboard
- 性能优化分析
- 问题定位
- 容量规划
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time
import psutil
import os


class ComponentStatus(Enum):
    """组件状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"      # 递增计数器
    GAUGE = "gauge"        # 当前值
    HISTOGRAM = "histogram" # 分布
    TIMER = "timer"        # 时间测量


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    process_count: int

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_used_mb": self.memory_used_mb,
            "memory_available_mb": self.memory_available_mb,
            "disk_percent": self.disk_percent,
            "process_count": self.process_count
        }


@dataclass
class AgentMetrics:
    """Agent指标"""
    agent_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    last_request_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def avg_duration_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2) if self.min_duration_ms != float('inf') else 0,
            "max_duration_ms": round(self.max_duration_ms, 2),
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }


@dataclass
class BusinessMetrics:
    """业务指标"""
    timestamp: datetime
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    active_sessions: int = 0
    total_queries: int = 0
    unique_users: int = 0

    @property
    def task_success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "task_success_rate": round(self.task_success_rate, 3),
            "active_sessions": self.active_sessions,
            "total_queries": self.total_queries,
            "unique_users": self.unique_users
        }


@dataclass
class TokenUsageMetrics:
    """Token使用指标"""
    endpoint: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
    max_input_tokens: int = 0
    max_output_tokens: int = 0
    last_request_time: Optional[datetime] = None

    def record(self, input_tokens: int, output_tokens: int):
        """记录token使用"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1
        self.avg_input_tokens = self.total_input_tokens / self.total_requests
        self.avg_output_tokens = self.total_output_tokens / self.total_requests
        if input_tokens > self.max_input_tokens:
            self.max_input_tokens = input_tokens
        if output_tokens > self.max_output_tokens:
            self.max_output_tokens = output_tokens
        self.last_request_time = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "endpoint": self.endpoint,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_requests": self.total_requests,
            "avg_input_tokens": round(self.avg_input_tokens, 2),
            "avg_output_tokens": round(self.avg_output_tokens, 2),
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }


@dataclass
class RAGQueryMetrics:
    """RAG查询指标"""
    query_type: str  # "semantic", "keyword", "hybrid"
    total_queries: int = 0
    total_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    reranking_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    avg_results_count: float = 0.0
    last_query_time: Optional[datetime] = None

    def record(self, latency_ms: float, retrieval_ms: float = 0, reranking_ms: float = 0, results_count: int = 0):
        """记录RAG查询"""
        self.total_queries += 1
        self.total_latency_ms += latency_ms
        self.retrieval_latency_ms += retrieval_ms
        self.reranking_latency_ms += reranking_ms
        self.avg_latency_ms = self.total_latency_ms / self.total_queries
        if latency_ms < self.min_latency_ms:
            self.min_latency_ms = latency_ms
        if latency_ms > self.max_latency_ms:
            self.max_latency_ms = latency_ms
        self.avg_results_count = (self.avg_results_count * (self.total_queries - 1) + results_count) / self.total_queries
        self.last_query_time = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "query_type": self.query_type,
            "total_queries": self.total_queries,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "min_latency_ms": round(self.min_latency_ms, 2) if self.min_latency_ms != float('inf') else 0,
            "max_latency_ms": round(self.max_latency_ms, 2),
            "avg_retrieval_ms": round(self.retrieval_latency_ms / max(1, self.total_queries), 2),
            "avg_reranking_ms": round(self.reranking_latency_ms / max(1, self.total_queries), 2),
            "avg_results_count": round(self.avg_results_count, 2),
            "last_query_time": self.last_query_time.isoformat() if self.last_query_time else None
        }


@dataclass
class CacheMetrics:
    """缓存指标"""
    cache_name: str
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    hit_rate: float = 0.0
    total_requests: int = 0

    def record_hit(self):
        """记录缓存命中"""
        self.hits += 1
        self.total_requests += 1
        self._update_hit_rate()

    def record_miss(self):
        """记录缓存未命中"""
        self.misses += 1
        self.total_requests += 1
        self._update_hit_rate()

    def record_eviction(self):
        """记录缓存淘汰"""
        self.evictions += 1

    def _update_hit_rate(self):
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests

    def to_dict(self) -> Dict:
        return {
            "cache_name": self.cache_name,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate, 4),
            "total_requests": self.total_requests
        }


@dataclass
class ErrorMetrics:
    """错误类型指标"""
    error_type: str
    count: int = 0
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    latest_message: str = ""

    def record_error(self, message: str = ""):
        """记录错误"""
        self.count += 1
        now = datetime.now()
        if self.first_occurrence is None:
            self.first_occurrence = now
        self.last_occurrence = now
        if message:
            self.latest_message = message

    def to_dict(self) -> Dict:
        return {
            "error_type": self.error_type,
            "count": self.count,
            "first_occurrence": self.first_occurrence.isoformat() if self.first_occurrence else None,
            "last_occurrence": self.last_occurrence.isoformat() if self.last_occurrence else None,
            "latest_message": self.latest_message
        }


class ComponentHealth:
    """组件健康状态"""

    def __init__(self, name: str):
        self.name = name
        self.status = ComponentStatus.UNKNOWN
        self.last_check = datetime.now()
        self.response_time_ms: float = 0.0
        self.error_message: Optional[str] = None

    def update(self, status: ComponentStatus, response_time_ms: float = 0.0, error: Optional[str] = None):
        self.status = status
        self.last_check = datetime.now()
        self.response_time_ms = response_time_ms
        self.error_message = error

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "last_check": self.last_check.isoformat(),
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message
        }


class MetricsCollector:
    """指标收集器

    【功能】
    - 收集系统指标
    - 追踪Agent性能
    - 记录业务指标
    - 健康检查
    - Token使用追踪
    - RAG查询追踪
    - 缓存命中率追踪
    - 错误类型统计
    """

    def __init__(self):
        # Agent指标存储
        self.agent_metrics: Dict[str, AgentMetrics] = {}

        # 业务指标
        self.business_metrics = BusinessMetrics(timestamp=datetime.now())

        # 组件健康状态
        self.components: Dict[str, ComponentHealth] = {}

        # 历史记录（固定大小）
        self.system_metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000

        # 请求计数
        self._request_counter = 0

        # Token使用指标 (by endpoint)
        self.token_metrics: Dict[str, TokenUsageMetrics] = {}

        # RAG查询指标 (by query type)
        self.rag_metrics: Dict[str, RAGQueryMetrics] = {}

        # 缓存指标 (by cache name)
        self.cache_metrics: Dict[str, CacheMetrics] = {}

        # 错误指标 (by error type)
        self.error_metrics: Dict[str, ErrorMetrics] = {}

    # ========== 系统指标 ==========

    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # 磁盘
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # 进程数
            process_count = len(psutil.pids())

            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=round(memory_used_mb, 2),
                memory_available_mb=round(memory_available_mb, 2),
                disk_percent=disk_percent,
                process_count=process_count
            )

            # 保存历史
            self.system_metrics_history.append(metrics)
            if len(self.system_metrics_history) > self.max_history_size:
                self.system_metrics_history.pop(0)

            return metrics

        except Exception as e:
            # 返回默认值
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                process_count=0
            )

    def get_system_metrics(self, duration_seconds: int = 60) -> Dict:
        """获取系统指标摘要

        Args:
            duration_seconds: 时间窗口（秒）

        Returns:
            系统指标统计
        """
        cutoff = datetime.now() - timedelta(seconds=duration_seconds)
        recent = [m for m in self.system_metrics_history if m.timestamp >= cutoff]

        if not recent:
            return {
                "period": f"{duration_seconds}s",
                "samples": 0,
                "cpu_avg": 0.0,
                "memory_avg": 0.0
            }

        return {
            "period": f"{duration_seconds}s",
            "samples": len(recent),
            "cpu_avg": round(sum(m.cpu_percent for m in recent) / len(recent), 2),
            "cpu_max": round(max(m.cpu_percent for m in recent), 2),
            "memory_avg": round(sum(m.memory_percent for m in recent) / len(recent), 2),
            "memory_max": round(max(m.memory_percent for m in recent), 2),
            "latest": recent[-1].to_dict()
        }

    # ========== Agent指标 ==========

    def record_agent_request(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool = True
    ):
        """记录Agent请求

        Args:
            agent_name: Agent名称
            duration_ms: 执行时长（毫秒）
            success: 是否成功
        """
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)

        metrics = self.agent_metrics[agent_name]
        metrics.total_requests += 1
        metrics.total_duration_ms += duration_ms
        metrics.last_request_time = datetime.now()

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # 更新min/max
        if duration_ms < metrics.min_duration_ms:
            metrics.min_duration_ms = duration_ms
        if duration_ms > metrics.max_duration_ms:
            metrics.max_duration_ms = duration_ms

    def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict:
        """获取Agent指标"""
        if agent_name:
            if agent_name in self.agent_metrics:
                return self.agent_metrics[agent_name].to_dict()
            return {}

        # 返回所有Agent指标
        return {
            name: metrics.to_dict()
            for name, metrics in self.agent_metrics.items()
        }

    def get_agent_leaderboard(self, sort_by: str = "total_requests", limit: int = 10) -> List[Dict]:
        """获取Agent排行

        Args:
            sort_by: 排序字段 (total_requests, success_rate, avg_duration_ms)
            limit: 返回数量
        """
        agents = list(self.agent_metrics.values())

        if sort_by == "success_rate":
            sorted_agents = sorted(agents, key=lambda a: a.success_rate, reverse=True)
        elif sort_by == "avg_duration_ms":
            sorted_agents = sorted(agents, key=lambda a: a.avg_duration_ms)
        else:
            sorted_agents = sorted(agents, key=lambda a: a.total_requests, reverse=True)

        return [a.to_dict() for a in sorted_agents[:limit]]

    # ========== 业务指标 ==========

    def record_task(self, success: bool = True):
        """记录任务"""
        self.business_metrics.total_tasks += 1
        if success:
            self.business_metrics.completed_tasks += 1
        else:
            self.business_metrics.failed_tasks += 1

    def record_query(self):
        """记录查询"""
        self.business_metrics.total_queries += 1

    def update_active_sessions(self, count: int):
        """更新活跃会话数"""
        self.business_metrics.active_sessions = count

    def update_unique_users(self, count: int):
        """更新独立用户数"""
        self.business_metrics.unique_users = count

    def get_business_metrics(self) -> Dict:
        """获取业务指标"""
        return self.business_metrics.to_dict()

    # ========== Token使用追踪 ==========

    def record_token_usage(
        self,
        endpoint: str,
        input_tokens: int,
        output_tokens: int
    ):
        """记录Token使用

        Args:
            endpoint: API端点
            input_tokens: 输入token数
            output_tokens: 输出token数
        """
        if endpoint not in self.token_metrics:
            self.token_metrics[endpoint] = TokenUsageMetrics(endpoint=endpoint)
        self.token_metrics[endpoint].record(input_tokens, output_tokens)

    def get_token_metrics(self, endpoint: Optional[str] = None) -> Dict:
        """获取Token指标"""
        if endpoint:
            if endpoint in self.token_metrics:
                return self.token_metrics[endpoint].to_dict()
            return {}
        return {
            name: metrics.to_dict()
            for name, metrics in self.token_metrics.items()
        }

    def get_total_token_usage(self) -> Dict:
        """获取总Token使用量"""
        total_input = sum(m.total_input_tokens for m in self.token_metrics.values())
        total_output = sum(m.total_output_tokens for m in self.token_metrics.values())
        total_requests = sum(m.total_requests for m in self.token_metrics.values())
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_requests": total_requests
        }

    # ========== RAG查询追踪 ==========

    def record_rag_query(
        self,
        query_type: str,
        latency_ms: float,
        retrieval_ms: float = 0,
        reranking_ms: float = 0,
        results_count: int = 0
    ):
        """记录RAG查询

        Args:
            query_type: 查询类型 (semantic/keyword/hybrid)
            latency_ms: 总延迟（毫秒）
            retrieval_ms: 检索延迟（毫秒）
            reranking_ms: 重排延迟（毫秒）
            results_count: 返回结果数量
        """
        if query_type not in self.rag_metrics:
            self.rag_metrics[query_type] = RAGQueryMetrics(query_type=query_type)
        self.rag_metrics[query_type].record(latency_ms, retrieval_ms, reranking_ms, results_count)

    def get_rag_metrics(self, query_type: Optional[str] = None) -> Dict:
        """获取RAG查询指标"""
        if query_type:
            if query_type in self.rag_metrics:
                return self.rag_metrics[query_type].to_dict()
            return {}
        return {
            name: metrics.to_dict()
            for name, metrics in self.rag_metrics.items()
        }

    def get_rag_summary(self) -> Dict:
        """获取RAG总览"""
        total_queries = sum(m.total_queries for m in self.rag_metrics.values())
        avg_latency = (
            sum(m.avg_latency_ms * m.total_queries for m in self.rag_metrics.values())
            / max(1, total_queries)
        )
        return {
            "total_queries": total_queries,
            "avg_latency_ms": round(avg_latency, 2),
            "by_type": self.get_rag_metrics()
        }

    # ========== 缓存追踪 ==========

    def record_cache_hit(self, cache_name: str):
        """记录缓存命中"""
        if cache_name not in self.cache_metrics:
            self.cache_metrics[cache_name] = CacheMetrics(cache_name=cache_name)
        self.cache_metrics[cache_name].record_hit()

    def record_cache_miss(self, cache_name: str):
        """记录缓存未命中"""
        if cache_name not in self.cache_metrics:
            self.cache_metrics[cache_name] = CacheMetrics(cache_name=cache_name)
        self.cache_metrics[cache_name].record_miss()

    def record_cache_eviction(self, cache_name: str):
        """记录缓存淘汰"""
        if cache_name not in self.cache_metrics:
            self.cache_metrics[cache_name] = CacheMetrics(cache_name=cache_name)
        self.cache_metrics[cache_name].record_eviction()

    def get_cache_metrics(self, cache_name: Optional[str] = None) -> Dict:
        """获取缓存指标"""
        if cache_name:
            if cache_name in self.cache_metrics:
                return self.cache_metrics[cache_name].to_dict()
            return {}
        return {
            name: metrics.to_dict()
            for name, metrics in self.cache_metrics.items()
        }

    def get_cache_summary(self) -> Dict:
        """获取缓存总览"""
        total_hits = sum(m.hits for m in self.cache_metrics.values())
        total_misses = sum(m.misses for m in self.cache_metrics.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = total_hits / max(1, total_requests)
        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests,
            "overall_hit_rate": round(overall_hit_rate, 4),
            "by_cache": self.get_cache_metrics()
        }

    # ========== 错误追踪 ==========

    def record_error(self, error_type: str, message: str = ""):
        """记录错误

        Args:
            error_type: 错误类型
            message: 错误消息
        """
        if error_type not in self.error_metrics:
            self.error_metrics[error_type] = ErrorMetrics(error_type=error_type)
        self.error_metrics[error_type].record_error(message)

    def get_error_metrics(self, error_type: Optional[str] = None) -> Dict:
        """获取错误指标"""
        if error_type:
            if error_type in self.error_metrics:
                return self.error_metrics[error_type].to_dict()
            return {}
        return {
            name: metrics.to_dict()
            for name, metrics in self.error_metrics.items()
        }

    def get_error_summary(self) -> Dict:
        """获取错误总览"""
        total_errors = sum(m.count for m in self.error_metrics.values())
        by_type = self.get_error_metrics()
        return {
            "total_errors": total_errors,
            "error_types_count": len(self.error_metrics),
            "by_type": by_type
        }

    # ========== 健康检查 ==========

    def register_component(self, name: str):
        """注册组件"""
        if name not in self.components:
            self.components[name] = ComponentHealth(name=name)

    def update_component_health(
        self,
        name: str,
        status: ComponentStatus,
        response_time_ms: float = 0.0,
        error: Optional[str] = None
    ):
        """更新组件健康状态"""
        if name in self.components:
            self.components[name].update(status, response_time_ms, error)

    def check_component_health(self, name: str) -> ComponentHealth:
        """检查组件健康状态"""
        if name not in self.components:
            self.components[name] = ComponentHealth(name=name)
        return self.components[name]

    def get_overall_health(self) -> Dict:
        """获取整体健康状态"""
        if not self.components:
            return {
                "status": ComponentStatus.UNKNOWN.value,
                "healthy_count": 0,
                "degraded_count": 0,
                "down_count": 0
            }

        healthy = sum(1 for c in self.components.values() if c.status == ComponentStatus.HEALTHY)
        degraded = sum(1 for c in self.components.values() if c.status == ComponentStatus.DEGRADED)
        down = sum(1 for c in self.components.values() if c.status == ComponentStatus.DOWN)

        # 整体状态判断
        if down > 0:
            overall = ComponentStatus.DOWN
        elif degraded > 0:
            overall = ComponentStatus.DEGRADED
        elif healthy == len(self.components):
            overall = ComponentStatus.HEALTHY
        else:
            overall = ComponentStatus.UNKNOWN

        return {
            "status": overall.value,
            "healthy_count": healthy,
            "degraded_count": degraded,
            "down_count": down,
            "total_components": len(self.components),
            "components": {
                name: comp.to_dict()
                for name, comp in self.components.items()
            }
        }

    # ========== 综合报告 ==========

    def get_full_report(self) -> Dict:
        """获取完整监控报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_metrics(),
            "agents": self.get_agent_metrics(),
            "agent_leaderboard": self.get_agent_leaderboard(),
            "business": self.get_business_metrics(),
            "health": self.get_overall_health(),
            "tokens": {
                "by_endpoint": self.get_token_metrics(),
                "totals": self.get_total_token_usage()
            },
            "rag": self.get_rag_summary(),
            "cache": self.get_cache_summary(),
            "errors": self.get_error_summary()
        }

    def reset(self):
        """重置所有指标"""
        self.agent_metrics.clear()
        self.business_metrics = BusinessMetrics(timestamp=datetime.now())
        self.system_metrics_history.clear()
        self.token_metrics.clear()
        self.rag_metrics.clear()
        self.cache_metrics.clear()
        self.error_metrics.clear()


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_type: str  # "cpu", "memory", "agent_success_rate", "agent_duration"
    threshold: float
    comparison: str  # "gt", "lt", "gte", "lte", "eq"
    duration_seconds: int = 0  # 持续时间（0表示立即触发）
    severity: AlertLevel = AlertLevel.WARNING
    enabled: bool = True

    def is_triggered(self, current_value: float, duration_seconds: int = 0) -> bool:
        """检查是否触发告警"""
        if not self.enabled:
            return False

        # 检查持续时间
        if self.duration_seconds > 0 and duration_seconds < self.duration_seconds:
            return False

        # 比较逻辑
        if self.comparison == "gt":
            return current_value > self.threshold
        elif self.comparison == "gte":
            return current_value >= self.threshold
        elif self.comparison == "lt":
            return current_value < self.threshold
        elif self.comparison == "lte":
            return current_value <= self.threshold
        elif self.comparison == "eq":
            return current_value == self.threshold
        return False


@dataclass
class Alert:
    """告警"""
    rule_name: str
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)


class AlertManager:
    """告警管理器

    【功能】
    - 管理告警规则
    - 检查阈值触发
    - 发送告警通知
    - 记录告警历史
    """

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.max_history_size = 100
        self._triggered_at: Dict[str, datetime] = {}  # 记录触发时间

        # 注册默认规则
        self._register_default_rules()

    def _register_default_rules(self):
        """注册默认告警规则"""
        default_rules = [
            AlertRule(
                name="high_cpu",
                metric_type="cpu",
                threshold=80.0,
                comparison="gte",
                severity=AlertLevel.WARNING,
                enabled=True
            ),
            AlertRule(
                name="critical_cpu",
                metric_type="cpu",
                threshold=95.0,
                comparison="gte",
                severity=AlertLevel.CRITICAL,
                enabled=True
            ),
            AlertRule(
                name="high_memory",
                metric_type="memory",
                threshold=85.0,
                comparison="gte",
                severity=AlertLevel.WARNING,
                enabled=True
            ),
            AlertRule(
                name="critical_memory",
                metric_type="memory",
                threshold=95.0,
                comparison="gte",
                severity=AlertLevel.CRITICAL,
                enabled=True
            ),
            AlertRule(
                name="low_agent_success_rate",
                metric_type="agent_success_rate",
                threshold=0.5,
                comparison="lt",
                severity=AlertLevel.ERROR,
                enabled=True
            ),
            AlertRule(
                name="high_agent_duration",
                metric_type="agent_duration_ms",
                threshold=5000.0,
                comparison="gte",
                duration_seconds=60,
                severity=AlertLevel.WARNING,
                enabled=True
            ),
            AlertRule(
                name="disk_full",
                metric_type="disk",
                threshold=90.0,
                comparison="gte",
                severity=AlertLevel.CRITICAL,
                enabled=True
            ),
        ]

        for rule in default_rules:
            self.rules[rule.name] = rule

    def add_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str) -> bool:
        """移除告警规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            return True
        return False

    def enable_rule(self, rule_name: str) -> bool:
        """启用规则"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
            return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """禁用规则"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            return True
        return False

    def check_metrics(self, system_metrics: SystemMetrics, agent_metrics: Dict[str, AgentMetrics]) -> List[Alert]:
        """检查指标并触发告警"""
        triggered_alerts = []

        # 检查系统指标
        self._check_system_metrics(system_metrics, triggered_alerts)

        # 检查Agent指标
        self._check_agent_metrics(agent_metrics, triggered_alerts)

        # 更新告警列表
        self.alerts = triggered_alerts

        # 记录历史
        self.alert_history.extend(triggered_alerts)
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]

        return triggered_alerts

    def _check_system_metrics(self, metrics: SystemMetrics, alerts: List[Alert]) -> None:
        """检查系统指标"""
        now = datetime.now()

        # CPU
        self._evaluate_rule("cpu", metrics.cpu_percent, now, alerts)

        # Memory
        self._evaluate_rule("memory", metrics.memory_percent, now, alerts)

        # Disk
        self._evaluate_rule("disk", metrics.disk_percent, now, alerts)

    def _check_agent_metrics(self, agent_metrics: Dict[str, AgentMetrics], alerts: List[Alert]) -> None:
        """检查Agent指标"""
        now = datetime.now()

        for name, metrics in agent_metrics.items():
            # 成功率
            if metrics.total_requests > 0:
                self._evaluate_rule(
                    "agent_success_rate",
                    metrics.success_rate,
                    now,
                    alerts,
                    metric_name=f"agent:{name}"
                )

            # 平均执行时间
            if metrics.avg_duration_ms > 0:
                self._evaluate_rule(
                    "agent_duration_ms",
                    metrics.avg_duration_ms,
                    now,
                    alerts,
                    metric_name=f"agent:{name}"
                )

    def _evaluate_rule(
        self,
        metric_type: str,
        current_value: float,
        now: datetime,
        alerts: List[Alert],
        metric_name: str = None
    ) -> None:
        """评估规则"""
        for rule in self.rules.values():
            if rule.metric_type != metric_type:
                continue

            # 检查是否触发
            triggered = rule.is_triggered(current_value)

            if triggered:
                # 记录触发时间
                rule_key = f"{rule.name}:{metric_name or metric_type}"
                if rule_key not in self._triggered_at:
                    self._triggered_at[rule_key] = now

                duration = (now - self._triggered_at[rule_key]).total_seconds()

                # 创建告警
                alert = Alert(
                    rule_name=rule.name,
                    level=rule.severity,
                    message=self._format_alert_message(rule, current_value, metric_name),
                    metric_name=metric_name or metric_type,
                    current_value=current_value,
                    threshold=rule.threshold,
                    timestamp=now
                )
                alerts.append(alert)
            else:
                # 重置触发时间
                rule_key = f"{rule.name}:{metric_name or metric_type}"
                if rule_key in self._triggered_at:
                    del self._triggered_at[rule_key]

    def _format_alert_message(self, rule: AlertRule, current_value: float, metric_name: str = None) -> str:
        """格式化告警消息"""
        metric_label = metric_name or rule.metric_type
        comparison_map = {
            "gt": "exceeded",
            "gte": "exceeded or reached",
            "lt": "below",
            "lte": "below or reached",
            "eq": "equals"
        }
        comparison_text = comparison_map.get(rule.comparison, "changed")
        return f"[{rule.severity.value.upper()}] {metric_label}: {current_value:.2f} {comparison_text} threshold {rule.threshold:.2f}"

    def get_active_alerts(self) -> List[Alert]:
        """获取当前告警"""
        return self.alerts

    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """获取告警历史"""
        return self.alert_history[-limit:]

    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """按级别筛选告警"""
        return [a for a in self.alert_history if a.level == level]

    def clear_alerts(self) -> None:
        """清除当前告警"""
        self.alerts.clear()

    def get_status_summary(self) -> Dict:
        """获取告警状态摘要"""
        if not self.alert_history:
            return {
                "total_rules": len(self.rules),
                "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
                "active_alerts": 0,
                "critical_count": 0,
                "error_count": 0,
                "warning_count": 0
            }

        active = self.alerts
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "active_alerts": len(active),
            "critical_count": sum(1 for a in active if a.level == AlertLevel.CRITICAL),
            "error_count": sum(1 for a in active if a.level == AlertLevel.ERROR),
            "warning_count": sum(1 for a in active if a.level == AlertLevel.WARNING),
            "info_count": sum(1 for a in active if a.level == AlertLevel.INFO),
            "last_alert_time": active[-1].timestamp.isoformat() if active else None
        }


# ========== 便捷函数和装饰器 ==========

# 全局实例
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_agent(agent_name: str):
    """Agent执行追踪装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                collector = get_metrics_collector()
                collector.record_agent_request(agent_name, duration_ms, success)
        return wrapper
    return decorator


class AgentTracker:
    """Agent追踪上下文管理器"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        collector = get_metrics_collector()
        collector.record_agent_request(self.agent_name, duration_ms, success)
        return False  # 不吞掉异常


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 获取指标收集器
collector = get_metrics_collector()

# 2. 注册需要监控的组件
collector.register_component("api")
collector.register_component("knowledge_base")
collector.register_component("agent_system")

# 3. 更新组件健康状态
collector.update_component_health(
    "api",
    ComponentStatus.HEALTHY,
    response_time_ms=45.2
)

# 4. 追踪Agent执行
collector.record_agent_request("dev", 123.5, success=True)
collector.record_agent_request("test", 89.3, success=True)

# 5. 记录业务指标
collector.record_task(success=True)
collector.record_query()
collector.update_active_sessions(15)

# 6. 获取完整报告
report = collector.get_full_report()

# 7. 使用装饰器追踪
@track_agent("doc")
async def generate_document():
    ...

# 8. 使用上下文管理器追踪
with AgentTracker("rag"):
    result = rag_agent.query("...")
"""


class MetricsExporter:
    """指标导出器

    支持将指标导出到不同格式
    """

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def to_prometheus_format(self) -> str:
        """导出为Prometheus格式"""
        lines = []
        report = self.collector.get_full_report()

        # System metrics
        lines.append(f'# HELP system_cpu_percent CPU使用率')
        lines.append(f'# TYPE system_cpu_percent gauge')
        lines.append(f'system_cpu_percent {report["system"]["cpu_avg"]}')

        lines.append(f'# HELP system_memory_percent 内存使用率')
        lines.append(f'# TYPE system_memory_percent gauge')
        lines.append(f'system_memory_percent {report["system"]["memory_avg"]}')

        # Agent metrics
        for name, metrics in report["agents"].items():
            lines.append(f'# HELP agent_requests_total Agent请求总数')
            lines.append(f'# TYPE agent_requests_total counter')
            lines.append(f'agent_requests_total{{agent="{name}"}} {metrics["total_requests"]}')

            lines.append(f'# HELP agent_success_rate Agent成功率')
            lines.append(f'# TYPE agent_success_rate gauge')
            lines.append(f'agent_success_rate{{agent="{name}"}} {metrics["success_rate"]}')

        return '\n'.join(lines)

    def to_json(self) -> Dict:
        """导出为JSON格式"""
        return self.collector.get_full_report()
