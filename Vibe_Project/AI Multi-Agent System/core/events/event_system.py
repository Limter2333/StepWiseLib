"""
事件通知系统 - Event Notification System
=======================================

【功能】
1. 事件发布/订阅 - 发布者-订阅者模式
2. 实时推送 - WebSocket实时推送事件
3. 事件历史 - 最近N条事件缓存
4. 事件过滤 - 按类型/来源过滤事件

【使用场景】
- Agent任务开始/完成时通知前端
- 系统异常时实时告警
- 任务进度实时更新
"""

from typing import Dict, Set, Callable, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import threading


class EventType(Enum):
    """事件类型"""
    # Agent事件
    AGENT_TASK_START = "agent_task_start"
    AGENT_TASK_COMPLETE = "agent_task_complete"
    AGENT_TASK_ERROR = "agent_task_error"
    AGENT_STATUS_CHANGE = "agent_status_change"

    # 系统事件
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"

    # RAG事件
    RAG_QUERY_START = "rag_query_start"
    RAG_QUERY_COMPLETE = "rag_query_complete"

    # 监控事件
    METRIC_THRESHOLD_EXCEEDED = "metric_threshold_exceeded"
    HEALTH_CHECK_FAILED = "health_check_failed"

    # 自定义事件
    CUSTOM = "custom"


@dataclass
class Event:
    """事件"""
    type: EventType
    source: str  # 事件来源，如 "dev_agent", "system"
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id
        }


class EventSubscriber:
    """事件订阅者"""

    def __init__(self, callback: Callable[[Event], None], event_filter: Optional[Set[EventType]] = None):
        self.callback = callback
        self.event_filter = event_filter  # None表示订阅所有事件

    def should_receive(self, event: Event) -> bool:
        if self.event_filter is None:
            return True
        return event.type in self.event_filter


class EventBus:
    """事件总线

    【架构】
    - 单例模式
    - 线程安全
    - 支持同步/异步订阅者
    """

    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'EventBus':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: List[EventSubscriber] = []
        self._subscriber_lock = threading.Lock()
        self._event_history: List[Event] = []
        self._max_history = 100
        self._history_lock = threading.Lock()

        # WebSocket广播接口
        self._websocket_broadcast: Optional[Callable[[Dict], None]] = None

        self._initialized = True

    def set_websocket_broadcast(self, broadcast_func: Callable[[Dict], None]):
        """设置WebSocket广播函数"""
        self._websocket_broadcast = broadcast_func

    def subscribe(self, callback: Callable[[Event], None], event_filter: Optional[Set[EventType]] = None) -> EventSubscriber:
        """订阅事件

        Args:
            callback: 事件回调函数
            event_filter: 要过滤的事件类型，None表示所有

        Returns:
            订阅者对象
        """
        subscriber = EventSubscriber(callback, event_filter)
        with self._subscriber_lock:
            self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: EventSubscriber):
        """取消订阅"""
        with self._subscriber_lock:
            self._subscribers.remove(subscriber)

    def publish(self, event: Event):
        """发布事件（同步）"""
        # 保存到历史
        with self._history_lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # 通知订阅者
        with self._subscriber_lock:
            for subscriber in self._subscribers:
                if subscriber.should_receive(event):
                    try:
                        subscriber.callback(event)
                    except Exception as e:
                        print(f"Event callback error: {e}")

        # WebSocket广播
        if self._websocket_broadcast:
            try:
                self._websocket_broadcast({
                    "type": "event",
                    "event": event.to_dict()
                })
            except Exception as e:
                print(f"WebSocket broadcast error: {e}")

    async def publish_async(self, event: Event):
        """发布事件（异步）"""
        # 保存到历史
        with self._history_lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # 通知订阅者
        with self._subscriber_lock:
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            if subscriber.should_receive(event):
                try:
                    if asyncio.iscoroutinefunction(subscriber.callback):
                        await subscriber.callback(event)
                    else:
                        subscriber.callback(event)
                except Exception as e:
                    print(f"Event callback error: {e}")

        # WebSocket广播
        if self._websocket_broadcast:
            try:
                self._websocket_broadcast({
                    "type": "event",
                    "event": event.to_dict()
                })
            except Exception as e:
                print(f"WebSocket broadcast error: {e}")

    def get_history(self, event_type: Optional[EventType] = None, limit: int = 50) -> List[Dict]:
        """获取事件历史"""
        with self._history_lock:
            events = list(self._event_history)

        if event_type:
            events = [e for e in events if e.type == event_type]

        return [e.to_dict() for e in events[-limit:]]

    def clear_history(self):
        """清空历史"""
        with self._history_lock:
            self._event_history.clear()


# ============ 便捷函数 ============

def get_event_bus() -> EventBus:
    """获取事件总线单例"""
    return EventBus()


def publish_event(event_type: EventType, source: str, data: Dict[str, Any]):
    """发布事件（便捷函数）"""
    event = Event(type=event_type, source=source, data=data)
    get_event_bus().publish(event)


def subscribe_events(callback: Callable[[Event], None], event_types: Optional[Set[EventType]] = None) -> EventSubscriber:
    """订阅事件（便捷函数）"""
    return get_event_bus().subscribe(callback, event_types)


# ============ Agent事件辅助 ============

def publish_agent_task_start(agent_id: str, task_id: str, task_type: str, description: str):
    """发布Agent任务开始事件"""
    publish_event(
        EventType.AGENT_TASK_START,
        source=agent_id,
        data={
            "task_id": task_id,
            "task_type": task_type,
            "description": description
        }
    )


def publish_agent_task_complete(agent_id: str, task_id: str, task_type: str, result_summary: str, duration_ms: float):
    """发布Agent任务完成事件"""
    publish_event(
        EventType.AGENT_TASK_COMPLETE,
        source=agent_id,
        data={
            "task_id": task_id,
            "task_type": task_type,
            "result_summary": result_summary,
            "duration_ms": duration_ms
        }
    )


def publish_agent_task_error(agent_id: str, task_id: str, task_type: str, error: str):
    """发布Agent任务错误事件"""
    publish_event(
        EventType.AGENT_TASK_ERROR,
        source=agent_id,
        data={
            "task_id": task_id,
            "task_type": task_type,
            "error": error
        }
    )


def publish_agent_status_change(agent_id: str, old_status: str, new_status: str):
    """发布Agent状态变更事件"""
    publish_event(
        EventType.AGENT_STATUS_CHANGE,
        source=agent_id,
        data={
            "old_status": old_status,
            "new_status": new_status
        }
    )


# ============ 使用示例 ============
"""
【基本用法】

from core.events.event_system import (
    get_event_bus, publish_event, EventType, Event
)

# 获取事件总线
bus = get_event_bus()

# 订阅事件
def handle_event(event: Event):
    print(f"收到事件: {event.type.value} from {event.source}")

bus.subscribe(handle_event, {EventType.AGENT_TASK_COMPLETE})

# 发布事件
publish_event(EventType.AGENT_TASK_START, "dev_agent", {"task_id": "123"})

【WebSocket集成】

from api.routes.websocket import manager

def ws_broadcast(message: dict):
    asyncio.run(manager.broadcast(message))

get_event_bus().set_websocket_broadcast(ws_broadcast)
"""


if __name__ == "__main__":
    print("Testing EventSystem...")

    bus = get_event_bus()

    # 订阅所有事件
    def on_event(event: Event):
        print(f"Event: {event.type.value} from {event.source}")

    bus.subscribe(on_event)

    # 发布测试事件
    publish_agent_task_start("dev_agent", "task-001", "code", "实现登录功能")
    publish_agent_task_complete("dev_agent", "task-001", "code", "完成", 1500)
    publish_agent_status_change("test_agent", "idle", "working")

    print(f"History: {bus.get_history()}")
    print("\nEventSystem OK")
