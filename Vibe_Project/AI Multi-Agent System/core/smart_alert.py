"""
智能告警系统 - Smart Alerting System
=====================================

【功能】
1. 告警规则 - 定义触发条件（事件类型+阈值）
2. 聚合抑制 - 同类告警合并，避免告警风暴
3. 告警级别 - CRITICAL/WARNING/INFO
4. 多渠道 - 日志、Webhook、事件总线
5. 静默窗口 - 临时屏蔽告警

【使用场景】
- Agent任务连续失败超过3次时告警
- 系统错误率超过阈值时告警
- RAG查询延迟过高时告警
"""

import time
from typing import Dict, Set, Optional, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    CRITICAL = "critical"  # 紧急，需要立即处理
    WARNING = "warning"     # 警告，需要关注
    INFO = "info"          # 信息


class AlertStatus(Enum):
    """告警状态"""
    FIRING = "firing"      # 正在触发
    RESOLVED = "resolved"  # 已解决
    SUPPRESSED = "suppressed"  # 被抑制


@dataclass
class Alert:
    """告警"""
    alert_id: str
    rule_name: str
    level: AlertLevel
    title: str
    description: str
    event_count: int = 1
    first_fired_at: float = field(default_factory=time.time)
    last_fired_at: float = field(default_factory=time.time)
    status: AlertStatus = AlertStatus.FIRING
    labels: Dict[str, str] = field(default_factory=dict)  # 标签用于聚合
    annotations: Dict[str, str] = field(default_factory=dict)  # 额外信息

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "rule_name": self.rule_name,
            "level": self.level.value,
            "title": self.title,
            "description": self.description,
            "event_count": self.event_count,
            "first_fired_at": self.first_fired_at,
            "last_fired_at": self.last_fired_at,
            "status": self.status.value,
            "labels": self.labels,
            "annotations": self.annotations
        }


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    event_type: str  # 触发的事件类型
    condition: Callable[[Dict], bool]  # 条件函数
    level: AlertLevel
    title_template: str  # 告警标题模板
    description_template: str  # 告警描述模板
    threshold: Optional[int] = None  # 触发阈值（如：连续3次）
    window_seconds: Optional[float] = None  # 时间窗口
    aggregation_key: Optional[str] = None  # 聚合键（如按agent_id聚合）
    cooldown_seconds: float = 60  # 冷却时间
    enabled: bool = True

    # 抑制配置
    max_alerts_per_window: Optional[int] = None  # 窗口内最大告警数
    suppress_duplicate_seconds: Optional[float] = None  # 重复告警抑制


class AlertChannel:
    """告警渠道基类"""

    def send(self, alert: Alert):
        raise NotImplementedError


class LogChannel(AlertChannel):
    """日志告警渠道"""

    def __init__(self, logger_name: str = "alerts"):
        self.logger = logging.getLogger(logger_name)

    def send(self, alert: Alert):
        log_level = {
            AlertLevel.CRITICAL: logging.CRITICAL,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.INFO: logging.INFO
        }.get(alert.level, logging.INFO)

        self.logger.log(
            log_level,
            f"[{alert.level.value.upper()}] {alert.title}: {alert.description}"
        )


class WebhookChannel(AlertChannel):
    """Webhook告警渠道"""

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        import hashlib, hmac, json
        self.webhook_url = webhook_url
        self.secret = secret

    async def send_async(self, alert: Alert):
        import httpx
        body = {
            "alert_id": alert.alert_id,
            "level": alert.level.value,
            "title": alert.title,
            "description": alert.description,
            "event_count": alert.event_count,
            "labels": alert.labels,
            "annotations": alert.annotations
        }

        headers = {"Content-Type": "application/json"}
        if self.secret:
            body_str = json.dumps(body)
            sig = hmac.new(self.secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()
            headers["X-Alert-Signature"] = f"sha256={sig}"

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.webhook_url, json=body, headers=headers, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send alert to webhook: {e}")

    def send(self, alert: Alert):
        # 同步版本使用事件总线
        from core.events import publish_event, EventType
        publish_event(EventType.METRIC_THRESHOLD_EXCEEDED, "alert_system", alert.to_dict())


class EventBusChannel(AlertChannel):
    """事件总线告警渠道"""

    def __init__(self):
        self._event_bus = None

    def _get_event_bus(self):
        if self._event_bus is None:
            from core.events import get_event_bus
            self._event_bus = get_event_bus()
        return self._event_bus

    def send(self, alert: Alert):
        from core.events import publish_event, EventType
        publish_event(
            EventType.SYSTEM_ERROR,
            source="alert_system",
            data=alert.to_dict()
        )


class AlertManager:
    """告警管理器

    【架构】
    - 规则引擎 - 评估事件是否触发告警
    - 聚合器 - 按labels聚合同类告警
    - 冷却追踪 - 避免重复告警
    - 多渠道分发 - 同时发送多个渠道
    """

    _instance: Optional['AlertManager'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'AlertManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}  # alert_id -> Alert
        self._alert_lock = threading.Lock()

        self._channels: List[AlertChannel] = [
            LogChannel(),
            EventBusChannel()
        ]

        # 事件跟踪（用于聚合）
        self._event_history: Dict[str, List[float]] = {}  # key -> [timestamp1, timestamp2...]
        self._history_lock = threading.Lock()

        # 冷却跟踪
        self._cooldowns: Dict[str, float] = {}  # rule_name -> last_fired_at
        self._suppression: Dict[str, float] = {}  # alert_id -> until_timestamp

        self._initialized = True

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._alert_lock:
            self._rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """移除告警规则"""
        with self._alert_lock:
            if rule_name in self._rules:
                del self._rules[rule_name]
                return True
        return False

    def list_rules(self) -> Dict[str, Dict]:
        """列出所有规则"""
        with self._alert_lock:
            return {
                name: {
                    "name": r.name,
                    "event_type": r.event_type,
                    "level": r.level.value,
                    "enabled": r.enabled
                }
                for name, r in self._rules.items()
            }

    def add_channel(self, channel: AlertChannel):
        """添加告警渠道"""
        self._channels.append(channel)

    def _should_fire(self, rule: AlertRule, event_data: Dict) -> bool:
        """检查是否应该触发告警"""
        if not rule.enabled:
            return False

        # 条件检查 - 不满足则直接跳过
        if not rule.condition(event_data):
            return False

        now = time.time()

        # 阈值检查 - 如果需要阈值，先累计计数
        if rule.threshold:
            key = f"{rule.name}:{event_data.get(rule.aggregation_key, 'default')}"
            with self._history_lock:
                # 清理过期
                if key in self._event_history:
                    self._event_history[key] = [
                        t for t in self._event_history[key]
                        if now - t < (rule.window_seconds or 60)
                    ]
                else:
                    self._event_history[key] = []

                self._event_history[key].append(now)
                count = len(self._event_history[key])

            # 阈值未达到，不触发告警也不冷却
            if count < rule.threshold:
                return False

        # 冷却检查 - 只在确定要触发时才检查
        last_fired = self._cooldowns.get(rule.name, 0)
        if now - last_fired < rule.cooldown_seconds:
            return False

        # 抑制检查
        if rule.suppress_duplicate_seconds:
            for alert in self._active_alerts.values():
                if alert.rule_name == rule.name:
                    if now - alert.last_fired_at < rule.suppress_duplicate_seconds:
                        return False

        return True

    def _format_template(self, template: str, event_data: Dict) -> str:
        """格式化模板"""
        try:
            return template.format(**event_data)
        except (KeyError, ValueError):
            return template

    def _generate_labels(self, rule: AlertRule, event_data: Dict) -> Dict[str, str]:
        """生成告警标签"""
        labels = {"rule": rule.name}
        if rule.aggregation_key and rule.aggregation_key in event_data:
            labels[rule.aggregation_key] = str(event_data[rule.aggregation_key])
        return labels

    def process_event(self, event_type: str, event_data: Dict):
        """处理事件"""
        with self._alert_lock:
            matching_rules = [
                r for r in self._rules.values()
                if r.event_type == event_type
            ]

        for rule in matching_rules:
            if self._should_fire(rule, event_data):
                self._fire_alert(rule, event_data)

    def _fire_alert(self, rule: AlertRule, event_data: Dict):
        """触发告警"""
        now = time.time()

        # 生成告警ID
        alert_id = f"{rule.name}:{now:.0f}"

        # 聚合键
        labels = self._generate_labels(rule, event_data)
        labels_key = "|".join(f"{k}={v}" for k, v in sorted(labels.items()))

        # 检查是否已有活跃告警可聚合
        with self._alert_lock:
            for existing in self._active_alerts.values():
                if (existing.rule_name == rule.name and
                    existing.labels == labels and
                    existing.status == AlertStatus.FIRING):

                    # 聚合更新
                    existing.event_count += 1
                    existing.last_fired_at = now
                    existing.description = self._format_template(
                        rule.description_template, event_data
                    )

                    # 更新冷却
                    self._cooldowns[rule.name] = now

                    # 发送到渠道
                    self._notify_channels(existing)
                    return

        # 获取历史事件计数（用于阈值触发的告警）
        initial_count = 1
        if rule.threshold and rule.aggregation_key:
            key = f"{rule.name}:{event_data.get(rule.aggregation_key, 'default')}"
            with self._history_lock:
                initial_count = len(self._event_history.get(key, [1]))

        # 创建新告警
        alert = Alert(
            alert_id=alert_id,
            rule_name=rule.name,
            level=rule.level,
            title=self._format_template(rule.title_template, event_data),
            description=self._format_template(rule.description_template, event_data),
            event_count=initial_count,
            labels=labels
        )

        with self._alert_lock:
            self._active_alerts[alert_id] = alert

        # 更新冷却
        self._cooldowns[rule.name] = now

        # 发送到渠道
        self._notify_channels(alert)

        logger.info(f"Fired alert: {alert.title}")

    def _notify_channels(self, alert: Alert):
        """通知所有渠道"""
        for channel in self._channels:
            try:
                channel.send(alert)
            except Exception as e:
                logger.error(f"Channel send error: {e}")

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        with self._alert_lock:
            if alert_id in self._active_alerts:
                self._active_alerts[alert_id].status = AlertStatus.RESOLVED
                return True
        return False

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Dict]:
        """获取活跃告警"""
        with self._alert_lock:
            alerts = [
                a.to_dict() for a in self._active_alerts.values()
                if a.status == AlertStatus.FIRING
            ]

        if level:
            alerts = [a for a in alerts if a["level"] == level.value]

        return alerts

    def get_alert_stats(self) -> Dict:
        """获取告警统计"""
        with self._alert_lock:
            firing = sum(1 for a in self._active_alerts.values() if a.status == AlertStatus.FIRING)
            resolved = sum(1 for a in self._active_alerts.values() if a.status == AlertStatus.RESOLVED)

            by_level = {}
            for a in self._active_alerts.values():
                lvl = a.level.value
                by_level[lvl] = by_level.get(lvl, 0) + 1

            return {
                "total_rules": len(self._rules),
                "active_alerts": firing,
                "resolved_alerts": resolved,
                "by_level": by_level
            }


# ============ 便捷函数 ============

def get_alert_manager() -> AlertManager:
    """获取告警管理器单例"""
    return AlertManager()


def add_alert_rule(
    name: str,
    event_type: str,
    condition: Callable[[Dict], bool],
    level: AlertLevel,
    title: str,
    description: str,
    **kwargs
):
    """添加告警规则（便捷函数）"""
    rule = AlertRule(
        name=name,
        event_type=event_type,
        condition=condition,
        level=level,
        title_template=title,
        description_template=description,
        **kwargs
    )
    get_alert_manager().add_rule(rule)


# ============ 预设规则 ============

def setup_default_rules():
    """设置默认告警规则"""
    manager = get_alert_manager()

    # Agent任务连续失败告警
    add_alert_rule(
        name="agent_task_error_streak",
        event_type="agent_task_error",
        condition=lambda d: True,
        level=AlertLevel.WARNING,
        title="Agent任务连续失败: {agent}",
        description="Agent {agent} 任务执行失败: {error}",
        threshold=3,
        window_seconds=300,
        aggregation_key="agent",
        cooldown_seconds=300
    )

    # 系统错误率告警
    add_alert_rule(
        name="system_error_rate",
        event_type="system_error",
        condition=lambda d: True,
        level=AlertLevel.CRITICAL,
        title="系统错误率过高",
        description="系统错误: {message}",
        threshold=5,
        window_seconds=60,
        cooldown_seconds=60
    )

    # 健康检查失败告警
    add_alert_rule(
        name="health_check_failed",
        event_type="health_check_failed",
        condition=lambda d: True,
        level=AlertLevel.WARNING,
        title="健康检查失败: {component}",
        description="组件 {component} 健康检查失败",
        aggregation_key="component",
        cooldown_seconds=300
    )


# ============ 使用示例 ============
"""
【基本用法】

from core.smart_alert import (
    AlertManager, AlertLevel, AlertRule, add_alert_rule
)

# 添加自定义规则
add_alert_rule(
    name="high_latency",
    event_type="agent_task_complete",
    condition=lambda d: d.get("duration_ms", 0) > 5000,
    level=AlertLevel.WARNING,
    title="Agent延迟过高",
    description="{agent} 任务耗时 {duration_ms}ms",
    cooldown_seconds=60
)

# 处理事件
manager = get_alert_manager()
manager.process_event("agent_task_complete", {
    "agent": "dev_agent",
    "task_id": "task-001",
    "duration_ms": 6000
})

【多渠道配置】

from core.smart_alert import AlertManager, WebhookChannel

manager = get_alert_manager()
manager.add_channel(WebhookChannel(
    webhook_url="https://hooks.slack.com/services/xxx",
    secret="webhook-secret"
))

【获取告警】

alerts = manager.get_active_alerts(AlertLevel.CRITICAL)
for alert in alerts:
    print(f"{alert['title']}: {alert['description']}")
"""


if __name__ == "__main__":
    print("Testing SmartAlert...")

    # 设置默认规则
    setup_default_rules()

    manager = get_alert_manager()

    # 模拟事件
    for i in range(5):
        manager.process_event("agent_task_error", {
            "agent": "dev_agent",
            "task_id": f"task-{i}",
            "error": "Connection timeout"
        })

    time.sleep(0.1)

    # 查看活跃告警
    alerts = manager.get_active_alerts()
    print(f"Active alerts: {len(alerts)}")

    # 查看统计
    stats = manager.get_alert_stats()
    print(f"Stats: {stats}")

    print("\nSmartAlert OK")
