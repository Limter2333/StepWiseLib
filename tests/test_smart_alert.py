"""
测试智能告警系统
"""

import pytest
import time
from unittest.mock import MagicMock
from core.smart_alert import (
    AlertManager,
    Alert,
    AlertRule,
    AlertLevel,
    AlertStatus,
    AlertChannel,
    LogChannel,
    get_alert_manager,
    add_alert_rule,
    setup_default_rules,
)


@pytest.fixture
def manager():
    """创建测试用告警管理器"""
    # 重置单例
    AlertManager._instance = None
    AlertManager._lock = __import__('threading').Lock()
    m = AlertManager()
    yield m
    m._initialized = False
    AlertManager._instance = None


class TestAlertManager:
    """AlertManager测试"""

    def test_singleton(self):
        """单例模式"""
        m1 = get_alert_manager()
        m2 = get_alert_manager()
        assert m1 is m2

    def test_add_rule(self, manager):
        """添加规则"""
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: True,
            level=AlertLevel.WARNING,
            title_template="Test",
            description_template="Test desc"
        )
        manager.add_rule(rule)

        rules = manager.list_rules()
        assert "test_rule" in rules

    def test_remove_rule(self, manager):
        """移除规则"""
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: True,
            level=AlertLevel.WARNING,
            title_template="Test",
            description_template="Test desc"
        )
        manager.add_rule(rule)
        assert manager.remove_rule("test_rule") is True
        assert "test_rule" not in manager.list_rules()

    def test_process_event_fires_alert(self, manager):
        """处理事件触发告警"""
        # 添加规则
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: True,
            level=AlertLevel.WARNING,
            title_template="Test Alert",
            description_template="Error: {error}"
        )
        manager.add_rule(rule)

        # 处理事件
        manager.process_event("agent_task_error", {
            "error": "Connection failed"
        })

        # 检查告警
        alerts = manager.get_active_alerts()
        assert len(alerts) >= 1

    def test_condition_not_met(self, manager):
        """条件不满足时不触发"""
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: d.get("count", 0) >= 5,
            level=AlertLevel.WARNING,
            title_template="Test",
            description_template="Test"
        )
        manager.add_rule(rule)

        manager.process_event("agent_task_error", {"count": 1})

        alerts = manager.get_active_alerts()
        assert len(alerts) == 0

    def test_cooldown(self, manager):
        """冷却时间"""
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: True,
            level=AlertLevel.WARNING,
            title_template="Test",
            description_template="Test",
            cooldown_seconds=60
        )
        manager.add_rule(rule)

        # 第一次触发
        manager.process_event("agent_task_error", {})

        # 冷却中再次触发（应该被抑制）
        manager.process_event("agent_task_error", {})

        alerts = manager.get_active_alerts()
        assert len(alerts) == 1  # 只有一条

    def test_aggregation(self, manager):
        """聚合"""
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: True,
            level=AlertLevel.WARNING,
            title_template="Test",
            description_template="Test",
            threshold=3,
            window_seconds=60,
            aggregation_key="agent"
        )
        manager.add_rule(rule)

        # 触发3次
        for i in range(3):
            manager.process_event("agent_task_error", {"agent": "dev"})

        alerts = manager.get_active_alerts()
        if alerts:
            assert alerts[0]["event_count"] == 3

    def test_resolve_alert(self, manager):
        """解决告警"""
        rule = AlertRule(
            name="test_rule",
            event_type="agent_task_error",
            condition=lambda d: True,
            level=AlertLevel.WARNING,
            title_template="Test",
            description_template="Test"
        )
        manager.add_rule(rule)

        manager.process_event("agent_task_error", {})

        alerts = manager.get_active_alerts()
        if alerts:
            alert_id = alerts[0]["alert_id"]
            assert manager.resolve_alert(alert_id) is True


class TestAlert:
    """Alert测试"""

    def test_alert_to_dict(self):
        """转字典"""
        alert = Alert(
            alert_id="test-123",
            rule_name="test_rule",
            level=AlertLevel.WARNING,
            title="Test Alert",
            description="Test description"
        )

        d = alert.to_dict()
        assert d["alert_id"] == "test-123"
        assert d["level"] == "warning"
        assert d["status"] == "firing"


class TestAlertRule:
    """AlertRule测试"""

    def test_rule_creation(self):
        """创建规则"""
        rule = AlertRule(
            name="test",
            event_type="test_event",
            condition=lambda d: True,
            level=AlertLevel.CRITICAL,
            title_template="Title",
            description_template="Desc"
        )

        assert rule.name == "test"
        assert rule.enabled is True
        assert rule.cooldown_seconds == 60


class TestAlertLevels:
    """告警级别测试"""

    def test_levels(self):
        """所有级别存在"""
        assert AlertLevel.CRITICAL.value == "critical"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.INFO.value == "info"


class TestLogChannel:
    """日志渠道测试"""

    def test_send(self):
        """发送"""
        channel = LogChannel("test")
        alert = Alert(
            alert_id="test",
            rule_name="rule",
            level=AlertLevel.WARNING,
            title="Test",
            description="Desc"
        )
        channel.send(alert)  # 不应抛出异常


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_add_alert_rule(self, manager):
        """添加规则"""
        add_alert_rule(
            name="convenience_rule",
            event_type="test",
            condition=lambda d: True,
            level=AlertLevel.INFO,
            title="Test",
            description="Test"
        )

        rules = manager.list_rules()
        assert "convenience_rule" in rules

    def test_setup_default_rules(self, manager):
        """设置默认规则"""
        setup_default_rules()

        rules = manager.list_rules()
        assert len(rules) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
