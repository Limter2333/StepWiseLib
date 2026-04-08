"""
测试事件通知系统
"""

import pytest
import time
from core.events import (
    EventBus,
    EventSubscriber,
    Event,
    EventType,
    get_event_bus,
    publish_event,
    subscribe_events,
    publish_agent_task_start,
    publish_agent_task_complete,
    publish_agent_task_error,
    publish_agent_status_change,
)


@pytest.fixture
def event_bus():
    """创建测试用事件总线"""
    bus = EventBus()
    bus.clear_history()
    yield bus
    bus.clear_history()


class TestEventBus:
    """EventBus测试"""

    def test_singleton(self):
        """单例模式"""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_publish_and_receive(self, event_bus):
        """发布和接收事件"""
        received = []

        def callback(event: Event):
            received.append(event)

        event_bus.subscribe(callback)
        publish_event(EventType.AGENT_TASK_START, "test_agent", {"task_id": "123"})

        assert len(received) == 1
        assert received[0].type == EventType.AGENT_TASK_START
        assert received[0].source == "test_agent"

    def test_event_filter(self, event_bus):
        """事件过滤"""
        received = []

        def callback(event: Event):
            received.append(event)

        event_bus.subscribe(callback, {EventType.AGENT_TASK_COMPLETE})
        publish_event(EventType.AGENT_TASK_START, "agent1", {})
        publish_event(EventType.AGENT_TASK_COMPLETE, "agent2", {})

        assert len(received) == 1
        assert received[0].type == EventType.AGENT_TASK_COMPLETE

    def test_multiple_subscribers(self, event_bus):
        """多个订阅者"""
        received1 = []
        received2 = []

        def callback1(event: Event):
            received1.append(event)

        def callback2(event: Event):
            received2.append(event)

        event_bus.subscribe(callback1)
        event_bus.subscribe(callback2)
        publish_event(EventType.SYSTEM_STARTUP, "system", {})

        assert len(received1) == 1
        assert len(received2) == 1

    def test_unsubscribe(self, event_bus):
        """取消订阅"""
        received = []

        def callback(event: Event):
            received.append(event)

        subscriber = event_bus.subscribe(callback)
        publish_event(EventType.AGENT_TASK_START, "agent", {})
        assert len(received) == 1

        event_bus.unsubscribe(subscriber)
        publish_event(EventType.AGENT_TASK_START, "agent", {})
        assert len(received) == 1  # 不再增加

    def test_event_history(self, event_bus):
        """事件历史"""
        publish_event(EventType.AGENT_TASK_START, "agent1", {"task": "1"})
        publish_event(EventType.AGENT_TASK_COMPLETE, "agent2", {"task": "2"})

        history = event_bus.get_history()
        assert len(history) == 2

    def test_event_history_filter(self, event_bus):
        """事件历史过滤"""
        publish_event(EventType.AGENT_TASK_START, "agent1", {})
        publish_event(EventType.AGENT_TASK_COMPLETE, "agent2", {})

        history = event_bus.get_history(EventType.AGENT_TASK_COMPLETE)
        assert len(history) == 1
        assert history[0]["type"] == "agent_task_complete"

    def test_history_limit(self, event_bus):
        """历史限制"""
        bus = EventBus.__new__(EventBus)
        bus._event_history = []
        bus._max_history = 5
        bus._history_lock = __import__('threading').Lock()

        for i in range(10):
            publish_event(EventType.CUSTOM, f"source_{i}", {"index": i})

        history = bus.get_history()
        assert len(history) == 5


class TestEventTypes:
    """事件类型测试"""

    def test_all_event_types_exist(self):
        """所有事件类型都存在"""
        assert EventType.AGENT_TASK_START.value == "agent_task_start"
        assert EventType.AGENT_TASK_COMPLETE.value == "agent_task_complete"
        assert EventType.AGENT_TASK_ERROR.value == "agent_task_error"
        assert EventType.AGENT_STATUS_CHANGE.value == "agent_status_change"
        assert EventType.SYSTEM_STARTUP.value == "system_startup"
        assert EventType.SYSTEM_SHUTDOWN.value == "system_shutdown"
        assert EventType.SYSTEM_ERROR.value == "system_error"
        assert EventType.RAG_QUERY_START.value == "rag_query_start"
        assert EventType.RAG_QUERY_COMPLETE.value == "rag_query_complete"
        assert EventType.METRIC_THRESHOLD_EXCEEDED.value == "metric_threshold_exceeded"
        assert EventType.HEALTH_CHECK_FAILED.value == "health_check_failed"
        assert EventType.CUSTOM.value == "custom"


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_publish_agent_task_start(self, event_bus):
        """发布Agent任务开始事件"""
        received = []

        def callback(event: Event):
            received.append(event)

        event_bus.subscribe(callback)
        publish_agent_task_start("dev_agent", "task-001", "code", "实现登录")

        assert len(received) == 1
        assert received[0].source == "dev_agent"
        assert received[0].data["task_id"] == "task-001"
        assert received[0].data["task_type"] == "code"

    def test_publish_agent_task_complete(self, event_bus):
        """发布Agent任务完成事件"""
        received = []

        def callback(event: Event):
            received.append(event)

        event_bus.subscribe(callback)
        publish_agent_task_complete("test_agent", "task-002", "test", "完成", 1500)

        assert len(received) == 1
        assert received[0].data["duration_ms"] == 1500

    def test_publish_agent_task_error(self, event_bus):
        """发布Agent任务错误事件"""
        received = []

        def callback(event: Event):
            received.append(event)

        event_bus.subscribe(callback)
        publish_agent_task_error("doc_agent", "task-003", "document", "文件不存在")

        assert len(received) == 1
        assert received[0].type == EventType.AGENT_TASK_ERROR
        assert "文件不存在" in received[0].data["error"]

    def test_publish_agent_status_change(self, event_bus):
        """发布Agent状态变更事件"""
        received = []

        def callback(event: Event):
            received.append(event)

        event_bus.subscribe(callback)
        publish_agent_status_change("pm_agent", "idle", "working")

        assert len(received) == 1
        assert received[0].data["old_status"] == "idle"
        assert received[0].data["new_status"] == "working"


class TestEvent:
    """Event数据类测试"""

    def test_event_to_dict(self):
        """事件转字典"""
        event = Event(
            type=EventType.AGENT_TASK_START,
            source="test",
            data={"key": "value"}
        )

        d = event.to_dict()
        assert d["type"] == "agent_task_start"
        assert d["source"] == "test"
        assert d["data"]["key"] == "value"
        assert "timestamp" in d


class TestEventSubscriber:
    """EventSubscriber测试"""

    def test_should_receive_all(self):
        """无过滤器接收所有事件"""
        subscriber = EventSubscriber(lambda e: None, None)
        event = Event(EventType.AGENT_TASK_START, "source", {})

        assert subscriber.should_receive(event) is True

    def test_should_receive_filtered(self):
        """有过滤器只接收指定事件"""
        subscriber = EventSubscriber(
            lambda e: None,
            {EventType.AGENT_TASK_COMPLETE, EventType.AGENT_TASK_ERROR}
        )

        event1 = Event(EventType.AGENT_TASK_START, "source", {})
        event2 = Event(EventType.AGENT_TASK_COMPLETE, "source", {})

        assert subscriber.should_receive(event1) is False
        assert subscriber.should_receive(event2) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
