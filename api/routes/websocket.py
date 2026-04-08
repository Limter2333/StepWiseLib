"""
WebSocket 路由 - 实时状态推送
=============================

集成了EventBus事件系统，支持：
- Agent任务状态实时推送
- 系统事件广播
- 实时指标更新
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import asyncio
import json
from datetime import datetime

router = APIRouter()

# 连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._event_bus = None

    def set_event_bus(self, event_bus):
        """设置事件总线用于集成"""
        self._event_bus = event_bus

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        await self.broadcast({
            "type": "connection",
            "status": "connected",
            "total_connections": len(self.active_connections),
            "timestamp": datetime.now().isoformat()
        })

    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            self.active_connections.discard(websocket)
        await self.broadcast({
            "type": "connection",
            "status": "disconnected",
            "total_connections": len(self.active_connections),
            "timestamp": datetime.now().isoformat()
        })

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        if not self.active_connections:
            return

        message_str = json.dumps(message, ensure_ascii=False)
        dead_connections = set()

        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except Exception:
                    dead_connections.add(connection)

            # 清理死连接
            self.active_connections -= dead_connections

    async def send_to(self, websocket: WebSocket, message: dict):
        """发送消息到指定连接"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception:
            pass


# 全局连接管理器
manager = ConnectionManager()


# Agent状态数据（由事件系统更新或模拟）
_agent_states: Dict = {
    "orchestrator": {"status": "active", "tasks": 0, "latency_ms": 0},
    "pm": {"status": "idle", "tasks": 0, "latency_ms": 0},
    "dev": {"status": "idle", "tasks": 0, "latency_ms": 0},
    "test": {"status": "idle", "tasks": 0, "latency_ms": 0},
    "doc": {"status": "idle", "tasks": 0, "latency_ms": 0},
    "rag": {"status": "idle", "tasks": 0, "latency_ms": 0},
    "conversation": {"status": "idle", "tasks": 0, "latency_ms": 0}
}

_metrics = {
    "cpu_percent": 0,
    "memory_percent": 0,
    "active_tasks": 0,
    "messages_per_sec": 0
}


def handle_agent_event(event):
    """处理来自EventBus的Agent事件"""
    import random

    event_data = event.data
    source = event.source

    if event.type.value == "agent_task_start":
        if source in _agent_states:
            _agent_states[source]["status"] = "working"
            _agent_states[source]["tasks"] = _agent_states[source].get("tasks", 0) + 1

    elif event.type.value == "agent_task_complete":
        if source in _agent_states:
            _agent_states[source]["status"] = "idle"
            _agent_states[source]["tasks"] = max(0, _agent_states[source].get("tasks", 1) - 1)

    elif event.type.value == "agent_status_change":
        new_status = event_data.get("new_status", "idle")
        if source in _agent_states:
            _agent_states[source]["status"] = new_status


# 初始化事件总线集成
_event_bus_initialized = False


def _ensure_event_bus_integration():
    """确保事件总线已集成"""
    global _event_bus_initialized
    if _event_bus_initialized:
        return

    try:
        from core.events import get_event_bus, EventType

        def ws_broadcast_wrapper(message: dict):
            if manager.active_connections:
                # 使用asyncio创建新事件循环来广播
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(manager.broadcast(message))
                    else:
                        loop.run_until_complete(manager.broadcast(message))
                except Exception:
                    pass

        event_bus = get_event_bus()
        event_bus.set_websocket_broadcast(ws_broadcast_wrapper)
        event_bus.subscribe(handle_agent_event, {
            EventType.AGENT_TASK_START,
            EventType.AGENT_TASK_COMPLETE,
            EventType.AGENT_STATUS_CHANGE
        })
        _event_bus_initialized = True
    except Exception as e:
        print(f"Event bus integration failed: {e}")


async def simulate_agent_updates():
    """模拟Agent状态更新（用于演示和WebSocket心跳）"""
    import random

    _ensure_event_bus_integration()

    while True:
        # 更新模拟数据
        _metrics["cpu_percent"] = random.randint(15, 45)
        _metrics["memory_percent"] = random.randint(30, 60)
        _metrics["messages_per_sec"] = random.randint(0, 10)

        for agent in _agent_states:
            if random.random() < 0.1:  # 10%概率切换状态
                current = _agent_states[agent]
                if current["status"] == "idle":
                    current["status"] = "working"
                    current["tasks"] = random.randint(1, 5)
                    current["latency_ms"] = random.randint(50, 200)
                else:
                    current["status"] = "idle"
                    current["tasks"] = 0
                    current["latency_ms"] = 0

        # 广播状态更新
        await manager.broadcast({
            "type": "agent_status",
            "agents": _agent_states,
            "metrics": _metrics,
            "timestamp": datetime.now().isoformat()
        })

        await asyncio.sleep(2)  # 每2秒更新一次


@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时状态端点

    客户端连接后接收:
    - agent_status: Agent状态更新
    - metrics: 系统指标
    - connection: 连接状态变化
    - event: 来自EventBus的事件
    """
    _ensure_event_bus_integration()
    await manager.connect(websocket)

    # 启动后台任务模拟更新
    update_task = asyncio.create_task(simulate_agent_updates())

    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif msg_type == "subscribe":
                    # 客户端订阅特定事件类型
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "subscribed_types": msg.get("types", []),
                        "timestamp": datetime.now().isoformat()
                    }))
                elif msg_type == "get_status":
                    # 客户端请求当前状态
                    await websocket.send_text(json.dumps({
                        "type": "agent_status",
                        "agents": _agent_states,
                        "metrics": _metrics,
                        "timestamp": datetime.now().isoformat()
                    }))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        update_task.cancel()
    except Exception:
        update_task.cancel()
        await manager.disconnect(websocket)


@router.get("/api/realtime/status")
async def get_realtime_status():
    """获取当前实时状态（HTTP轮询备选）"""
    return {
        "agents": _agent_states,
        "metrics": _metrics,
        "connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }
