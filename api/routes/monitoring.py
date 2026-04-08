"""
Monitoring API 路由
==================

提供系统监控指标、健康检查、告警管理接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import time

from monitoring.metrics_collector import (
    get_metrics_collector,
    MetricsCollector,
    MetricsExporter,
    AlertManager,
    AlertLevel,
    AlertRule,
    ComponentStatus
)

router = APIRouter()


# ========== 数据模型 ==========

class SystemMetricsResponse(BaseModel):
    """系统指标响应"""
    period: str
    samples: int
    cpu_avg: float
    cpu_max: Optional[float] = None
    memory_avg: float
    memory_max: Optional[float] = None
    latest: Optional[Dict] = None


class AgentMetricsResponse(BaseModel):
    """Agent指标响应"""
    agent_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    last_request_time: Optional[str]


class BusinessMetricsResponse(BaseModel):
    """业务指标响应"""
    timestamp: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    task_success_rate: float
    active_sessions: int
    total_queries: int
    unique_users: int


class ComponentHealthResponse(BaseModel):
    """组件健康状态响应"""
    name: str
    status: str
    last_check: str
    response_time_ms: float
    error_message: Optional[str]


class OverallHealthResponse(BaseModel):
    """整体健康状态响应"""
    status: str
    healthy_count: int
    degraded_count: int
    down_count: int
    total_components: Optional[int] = 0
    components: Optional[Dict[str, ComponentHealthResponse]] = None


class AlertResponse(BaseModel):
    """告警响应"""
    rule_name: str
    level: str
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: str


class AlertRuleCreate(BaseModel):
    """创建告警规则请求"""
    name: str
    metric_type: str
    threshold: float
    comparison: str
    duration_seconds: int = 0
    severity: str = "warning"
    enabled: bool = True


class MonitoringReportResponse(BaseModel):
    """完整监控报告响应"""
    timestamp: str
    system: Dict
    agents: Dict[str, AgentMetricsResponse]
    agent_leaderboard: List[Dict]
    business: Dict
    health: Dict
    active_alerts: List[AlertResponse]
    tokens: Optional[Dict] = None
    rag: Optional[Dict] = None
    cache: Optional[Dict] = None
    errors: Optional[Dict] = None


# ========== 全局实例 ==========

_collector = get_metrics_collector()
_alert_manager = AlertManager()


# ========== 系统指标 ==========

@router.get("/metrics/system")
async def get_system_metrics(duration_seconds: int = 60) -> SystemMetricsResponse:
    """获取系统指标

    Args:
        duration_seconds: 时间窗口（秒）

    Returns:
        系统指标统计
    """
    return _collector.get_system_metrics(duration_seconds)


@router.get("/metrics/system/collect")
async def collect_system_metrics():
    """手动触发系统指标收集

    Returns:
        当前系统指标
    """
    metrics = _collector.collect_system_metrics()
    return metrics.to_dict()


# ========== Agent指标 ==========

@router.get("/metrics/agents")
async def get_agents_metrics(agent_name: Optional[str] = None) -> Dict[str, AgentMetricsResponse]:
    """获取Agent指标

    Args:
        agent_name: 可选的Agent名称过滤

    Returns:
        Agent指标字典
    """
    return _collector.get_agent_metrics(agent_name)


@router.get("/metrics/agents/leaderboard")
async def get_agent_leaderboard(
    sort_by: str = "total_requests",
    limit: int = 10
) -> List[Dict]:
    """获取Agent排行

    Args:
        sort_by: 排序字段 (total_requests, success_rate, avg_duration_ms)
        limit: 返回数量

    Returns:
        排序后的Agent列表
    """
    return _collector.get_agent_leaderboard(sort_by, limit)


# ========== 业务指标 ==========

@router.get("/metrics/business")
async def get_business_metrics() -> BusinessMetricsResponse:
    """获取业务指标

    Returns:
        业务指标
    """
    return _collector.get_business_metrics()


@router.post("/metrics/business/task")
async def record_task(success: bool = True):
    """记录任务完成

    Args:
        success: 任务是否成功

    Returns:
        成功状态
    """
    _collector.record_task(success)
    return {"success": True}


@router.post("/metrics/business/query")
async def record_query():
    """记录查询

    Returns:
        成功状态
    """
    _collector.record_query()
    return {"success": True}


@router.post("/metrics/business/sessions")
async def update_sessions(count: int):
    """更新活跃会话数

    Args:
        count: 活跃会话数

    Returns:
        成功状态
    """
    _collector.update_active_sessions(count)
    return {"success": True}


# ========== 健康检查 ==========

@router.get("/health/components")
async def get_components_health() -> List[ComponentHealthResponse]:
    """获取所有组件健康状态

    Returns:
        组件健康状态列表
    """
    health = _collector.get_overall_health()
    components = health.get("components", {})
    return [
        ComponentHealthResponse(**comp)
        for comp in components.values()
    ]


@router.get("/health/overall")
async def get_overall_health() -> OverallHealthResponse:
    """获取整体健康状态

    Returns:
        整体健康状态
    """
    return _collector.get_overall_health()


@router.post("/health/components/{name}")
async def update_component_health(
    name: str,
    status: str,
    response_time_ms: float = 0.0,
    error: Optional[str] = None
):
    """更新组件健康状态

    Args:
        name: 组件名称
        status: 状态 (healthy, degraded, down, unknown)
        response_time_ms: 响应时间（毫秒）
        error: 错误信息

    Returns:
        成功状态
    """
    try:
        status_enum = ComponentStatus[status.upper()]
    except KeyError:
        status_enum = ComponentStatus.UNKNOWN

    _collector.register_component(name)
    _collector.update_component_health(name, status_enum, response_time_ms, error)
    return {"success": True}


# ========== 告警管理 ==========

@router.get("/alerts")
async def get_active_alerts() -> List[AlertResponse]:
    """获取当前告警

    Returns:
        当前告警列表
    """
    alerts = _alert_manager.get_active_alerts()
    return [
        AlertResponse(
            rule_name=a.rule_name,
            level=a.level.value,
            message=a.message,
            metric_name=a.metric_name,
            current_value=a.current_value,
            threshold=a.threshold,
            timestamp=a.timestamp.isoformat()
        )
        for a in alerts
    ]


@router.get("/alerts/history")
async def get_alert_history(limit: int = 50) -> List[AlertResponse]:
    """获取告警历史

    Args:
        limit: 返回数量

    Returns:
        告警历史列表
    """
    alerts = _alert_manager.get_alert_history(limit)
    return [
        AlertResponse(
            rule_name=a.rule_name,
            level=a.level.value,
            message=a.message,
            metric_name=a.metric_name,
            current_value=a.current_value,
            threshold=a.threshold,
            timestamp=a.timestamp.isoformat()
        )
        for a in alerts
    ]


@router.get("/alerts/rules")
async def get_alert_rules() -> List[Dict]:
    """获取所有告警规则

    Returns:
        告警规则列表
    """
    return [
        {
            "name": r.name,
            "metric_type": r.metric_type,
            "threshold": r.threshold,
            "comparison": r.comparison,
            "duration_seconds": r.duration_seconds,
            "severity": r.severity.value,
            "enabled": r.enabled
        }
        for r in _alert_manager.rules.values()
    ]


@router.post("/alerts/rules")
async def create_alert_rule(rule: AlertRuleCreate):
    """创建告警规则

    Args:
        rule: 告警规则

    Returns:
        成功状态
    """
    try:
        severity = AlertLevel[rule.severity.upper()]
    except KeyError:
        severity = AlertLevel.WARNING

    alert_rule = AlertRule(
        name=rule.name,
        metric_type=rule.metric_type,
        threshold=rule.threshold,
        comparison=rule.comparison,
        duration_seconds=rule.duration_seconds,
        severity=severity,
        enabled=rule.enabled
    )
    _alert_manager.add_rule(alert_rule)
    return {"success": True, "rule_name": rule.name}


@router.delete("/alerts/rules/{rule_name}")
async def delete_alert_rule(rule_name: str):
    """删除告警规则

    Args:
        rule_name: 规则名称

    Returns:
        成功状态
    """
    success = _alert_manager.remove_rule(rule_name)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"success": True}


@router.patch("/alerts/rules/{rule_name}")
async def update_alert_rule(rule_name: str, enabled: bool):
    """更新告警规则状态

    Args:
        rule_name: 规则名称
        enabled: 是否启用

    Returns:
        成功状态
    """
    if enabled:
        success = _alert_manager.enable_rule(rule_name)
    else:
        success = _alert_manager.disable_rule(rule_name)

    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"success": True}


@router.get("/alerts/status")
async def get_alert_status() -> Dict:
    """获取告警状态摘要

    Returns:
        告警状态摘要
    """
    return _alert_manager.get_status_summary()


# ========== 综合报告 ==========

@router.get("/report")
async def get_full_report() -> MonitoringReportResponse:
    """获取完整监控报告

    Returns:
        完整监控报告
    """
    # 收集系统指标
    system_metrics = _collector.collect_system_metrics()

    # 检查告警
    _alert_manager.check_metrics(system_metrics, _collector.agent_metrics)

    # 获取完整报告
    report = _collector.get_full_report()

    # 添加活跃告警
    active_alerts = _alert_manager.get_active_alerts()

    return {
        "timestamp": datetime.now().isoformat(),
        "system": report["system"],
        "agents": report["agents"],
        "agent_leaderboard": report["agent_leaderboard"],
        "business": report["business"],
        "health": report["health"],
        "active_alerts": [
            {
                "rule_name": a.rule_name,
                "level": a.level.value,
                "message": a.message,
                "metric_name": a.metric_name,
                "current_value": a.current_value,
                "threshold": a.threshold,
                "timestamp": a.timestamp.isoformat()
            }
            for a in active_alerts
        ],
        "tokens": report.get("tokens", {}),
        "rag": report.get("rag", {}),
        "cache": report.get("cache", {}),
        "errors": report.get("errors", {})
    }


# ========== Prometheus 指标导出 ==========

@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """获取Prometheus格式的指标

    Returns:
        Prometheus文本格式的指标数据
    """
    exporter = MetricsExporter(_collector)
    return exporter.to_prometheus_format()


@router.get("/metrics/export")
async def get_exported_metrics(format: str = "json"):
    """导出指标数据

    Args:
        format: 导出格式 (json/prometheus)

    Returns:
        指定格式的指标数据
    """
    exporter = MetricsExporter(_collector)

    if format == "prometheus":
        return exporter.to_prometheus_format()
    else:
        return exporter.to_json()


# ========== 便捷函数 ==========

@router.post("/track/agent/{agent_name}")
async def track_agent_request(
    agent_name: str,
    duration_ms: float,
    success: bool = True
):
    """追踪Agent请求（手动）

    Args:
        agent_name: Agent名称
        duration_ms: 执行时长（毫秒）
        success: 是否成功

    Returns:
        成功状态
    """
    _collector.record_agent_request(agent_name, duration_ms, success)
    return {"success": True}

# ========== API使用统计 ==========

from monitoring.usage_stats import get_usage_stats, CostEstimator

_usage_stats = get_usage_stats()


class UsageRecordRequest(BaseModel):
    """使用记录请求"""
    endpoint: str
    method: str
    duration_ms: float
    token_count: int
    status_code: int
    session_id: Optional[str] = None
    user_id: Optional[str] = None


@router.get("/usage/total")
async def get_usage_total():
    """获取API使用总统计

    Returns:
        总调用量、Token消耗、费用估算
    """
    stats = _usage_stats.get_total_stats()
    return {
        "success": True,
        **stats
    }


@router.get("/usage/endpoints")
async def get_usage_by_endpoint(endpoint: Optional[str] = None):
    """获取端点使用统计

    Args:
        endpoint: 可选的端点过滤

    Returns:
        端点统计列表
    """
    stats = _usage_stats.get_endpoint_stats(endpoint)
    return {
        "success": True,
        "endpoints": [
            {
                "endpoint": s.endpoint,
                "method": s.method,
                "call_count": s.call_count,
                "total_tokens": s.total_tokens,
                "avg_tokens": round(s.avg_tokens, 2),
                "avg_duration_ms": round(s.avg_duration_ms, 2),
                "p50_ms": round(s.p50_ms, 2),
                "p95_ms": round(s.p95_ms, 2),
                "p99_ms": round(s.p99_ms, 2),
                "error_rate": round(s.error_rate * 100, 2),
                "last_called": s.last_called.isoformat() if s.last_called else None
            }
            for s in stats.values()
        ]
    }


@router.get("/usage/session/{session_id}")
async def get_usage_by_session(session_id: str):
    """获取会话使用统计

    Args:
        session_id: 会话ID

    Returns:
        会话统计
    """
    stats = _usage_stats.get_session_stats(session_id)
    return {
        "success": True,
        **stats
    }


@router.post("/usage/record")
async def record_usage(request: UsageRecordRequest):
    """记录API使用

    Args:
        request: 使用记录

    Returns:
        成功状态和费用估算
    """
    cost = _usage_stats.record(
        endpoint=request.endpoint,
        method=request.method,
        duration_ms=request.duration_ms,
        token_count=request.token_count,
        status_code=request.status_code,
        session_id=request.session_id,
        user_id=request.user_id
    )
    return {
        "success": True,
        "cost_estimate_usd": round(cost, 6)
    }


@router.delete("/usage/clear")
async def clear_usage():
    """清空使用统计"""
    _usage_stats.clear()
    return {"success": True, "message": "Usage stats cleared"}


@router.get("/usage/cost/estimate")
async def get_cost_estimate(input_tokens: int, output_tokens: int):
    """获取成本估算

    Args:
        input_tokens: 输入Token数
        output_tokens: 输出Token数

    Returns:
        成本估算
    """
    cost = CostEstimator.estimate_cost(input_tokens, output_tokens)
    return {
        "success": True,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
        "pricing": {
            "input_per_1m": CostEstimator.INPUT_COST_PER_M,
            "output_per_1m": CostEstimator.OUTPUT_COST_PER_M
        }
    }
