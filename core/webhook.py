"""
Webhook系统 - Webhook Delivery System
======================================

【功能】
1. Webhook注册 - 注册多个Webhook URL和事件类型
2. 异步投递 - 后台线程异步发送HTTP POST请求
3. 重试机制 - 失败后自动重试（指数退避）
4. 签名验证 - 支持HMAC-SHA256签名
5. 事件过滤 - 按事件类型过滤

【使用场景】
- Agent任务完成时通知外部系统
- 系统异常时发送告警到Slack/邮件
- 数据变更时触发CI/CD Pipeline
"""

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from typing import Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging

import httpx

logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """投递状态"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookDelivery:
    """Webhook投递记录"""
    delivery_id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status: DeliveryStatus
    attempts: int = 0
    max_attempts: int = 3
    created_at: float = field(default_factory=time.time)
    last_attempt_at: Optional[float] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Webhook:
    """Webhook配置"""
    id: str
    url: str
    events: Set[str]  # 订阅的事件类型
    secret: Optional[str] = None  # 用于签名
    headers: Dict[str, str] = field(default_factory=dict)  # 自定义请求头
    enabled: bool = True
    description: Optional[str] = None


class WebhookManager:
    """Webhook管理器

    【架构】
    - 注册表管理所有Webhook
    - 事件过滤器只投递订阅的事件
    - 异步投递队列
    - 重试线程处理失败投递
    """

    def __init__(self):
        self._webhooks: Dict[str, Webhook] = {}
        self._webhook_lock = threading.Lock()
        self._deliveries: Dict[str, WebhookDelivery] = {}
        self._delivery_lock = threading.Lock()

        # 投递队列
        self._delivery_queue: asyncio.Queue = asyncio.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._shutdown = False

        # HTTP客户端
        self._client: Optional[httpx.AsyncClient] = None

        # 事件总线集成
        self._event_bus = None

    def _ensure_client(self):
        """确保HTTP客户端已创建"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)

    def register_webhook(
        self,
        url: str,
        events: Set[str],
        secret: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> str:
        """注册Webhook

        Args:
            url: Webhook URL
            events: 订阅的事件类型
            secret: 签名密钥（可选）
            headers: 自定义请求头
            description: 描述

        Returns:
            webhook_id
        """
        webhook_id = str(uuid.uuid4())[:8]

        with self._webhook_lock:
            self._webhooks[webhook_id] = Webhook(
                id=webhook_id,
                url=url,
                events=events,
                secret=secret,
                headers=headers or {},
                description=description
            )

        logger.info(f"Registered webhook {webhook_id} for {len(events)} events")
        return webhook_id

    def unregister_webhook(self, webhook_id: str) -> bool:
        """注销Webhook"""
        with self._webhook_lock:
            if webhook_id in self._webhooks:
                del self._webhooks[webhook_id]
                logger.info(f"Unregistered webhook {webhook_id}")
                return True
        return False

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """获取Webhook"""
        with self._webhook_lock:
            return self._webhooks.get(webhook_id)

    def list_webhooks(self) -> Dict[str, Dict]:
        """列出所有Webhook"""
        with self._webhook_lock:
            return {
                wid: {
                    "id": w.id,
                    "url": w.url,
                    "events": list(w.events),
                    "enabled": w.enabled,
                    "description": w.description
                }
                for wid, w in self._webhooks.items()
            }

    def update_webhook(self, webhook_id: str, enabled: Optional[bool] = None) -> bool:
        """更新Webhook"""
        with self._webhook_lock:
            if webhook_id in self._webhooks:
                if enabled is not None:
                    self._webhooks[webhook_id].enabled = enabled
                return True
        return False

    def _generate_signature(self, payload: str, secret: str) -> str:
        """生成HMAC-SHA256签名"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def _deliver(self, delivery: WebhookDelivery, webhook: Webhook):
        """执行单次投递"""
        delivery.attempts += 1
        delivery.last_attempt_at = time.time()

        # 构建请求体
        body = {
            "event": delivery.event_type,
            "webhook_id": webhook.id,
            "delivery_id": delivery.delivery_id,
            "timestamp": time.time(),
            "data": delivery.payload
        }
        body_str = json.dumps(body, ensure_ascii=False)

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AI-Agent-Webhook/1.0",
            "X-Webhook-ID": webhook.id,
            "X-Delivery-ID": delivery.delivery_id,
            "X-Event-Type": delivery.event_type
        }

        # 添加签名
        if webhook.secret:
            signature = self._generate_signature(body_str, webhook.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # 合并自定义头
        headers.update(webhook.headers)

        try:
            self._ensure_client()
            response = await self._client.post(
                webhook.url,
                content=body_str,
                headers=headers
            )
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:500] if response.text else None

            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.SUCCESS
                logger.info(f"Webhook {webhook.id} delivery {delivery.delivery_id} succeeded")
            else:
                delivery.status = DeliveryStatus.FAILED
                delivery.error = f"HTTP {response.status_code}"
                logger.warning(f"Webhook {webhook.id} delivery failed: {response.status_code}")

        except Exception as e:
            delivery.status = DeliveryStatus.FAILED
            delivery.error = str(e)
            delivery.response_body = None
            logger.error(f"Webhook {webhook.id} delivery error: {e}")

    async def _delivery_worker(self):
        """投递工作线程"""
        while not self._shutdown:
            try:
                delivery_id = await asyncio.wait_for(
                    self._delivery_queue.get(),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            with self._delivery_lock:
                delivery = self._deliveries.get(delivery_id)
                if not delivery:
                    continue

            webhook_id = delivery.webhook_id
            with self._webhook_lock:
                webhook = self._webhooks.get(webhook_id)
                if not webhook or not webhook.enabled:
                    continue

            await self._deliver(delivery, webhook)

            # 如果失败且还有重试机会，加入重试队列
            if delivery.status == DeliveryStatus.FAILED and delivery.attempts < delivery.max_attempts:
                delivery.status = DeliveryStatus.RETRYING
                delay = 2 ** delivery.attempts  # 指数退避: 2, 4, 8秒
                logger.info(f"Scheduling retry {delivery.attempts + 1} in {delay}s")
                asyncio.create_task(self._schedule_retry(delivery_id, delay))

    async def _schedule_retry(self, delivery_id: str, delay: float):
        """调度重试"""
        await asyncio.sleep(delay)
        if not self._shutdown:
            self._delivery_queue.put_nowait(delivery_id)

    def queue_delivery(self, event_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """将投递加入队列

        Args:
            event_type: 事件类型
            payload: 事件数据

        Returns:
            delivery_id 或 None（如果没有匹配的Webhook）
        """
        matching_webhooks = []

        with self._webhook_lock:
            for webhook in self._webhooks.values():
                if webhook.enabled and event_type in webhook.events:
                    matching_webhooks.append(webhook)

        if not matching_webhooks:
            return None

        delivery_ids = []
        for webhook in matching_webhooks:
            delivery_id = str(uuid.uuid4())[:8]
            delivery = WebhookDelivery(
                delivery_id=delivery_id,
                webhook_id=webhook.id,
                event_type=event_type,
                payload=payload,
                status=DeliveryStatus.PENDING
            )

            with self._delivery_lock:
                self._deliveries[delivery_id] = delivery

            self._delivery_queue.put_nowait(delivery_id)
            delivery_ids.append(delivery_id)

        return delivery_ids[0] if len(delivery_ids) == 1 else delivery_ids

    def get_delivery_status(self, delivery_id: str) -> Optional[Dict]:
        """获取投递状态"""
        with self._delivery_lock:
            delivery = self._deliveries.get(delivery_id)
            if not delivery:
                return None

            return {
                "delivery_id": delivery.delivery_id,
                "webhook_id": delivery.webhook_id,
                "event_type": delivery.event_type,
                "status": delivery.status.value,
                "attempts": delivery.attempts,
                "max_attempts": delivery.max_attempts,
                "created_at": delivery.created_at,
                "last_attempt_at": delivery.last_attempt_at,
                "response_status": delivery.response_status,
                "error": delivery.error
            }

    def start(self):
        """启动投递工作线程"""
        if self._worker_thread is not None:
            return

        self._shutdown = False
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()
        logger.info("Webhook delivery worker started")

    def _run_worker(self):
        """运行工作线程（同步入口）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._delivery_worker())
        finally:
            loop.close()

    def shutdown(self):
        """关闭Webhook系统"""
        self._shutdown = True
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        if self._client:
            asyncio.run(self._client.aclose())


# ============ 便捷函数 ============

_manager: Optional[WebhookManager] = None
_manager_lock = threading.Lock()


def get_webhook_manager() -> WebhookManager:
    """获取Webhook管理器单例"""
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = WebhookManager()
                _manager.start()
    return _manager


def register_webhook(
    url: str,
    events: Set[str],
    secret: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    description: Optional[str] = None
) -> str:
    """注册Webhook（便捷函数）"""
    return get_webhook_manager().register_webhook(url, events, secret, headers, description)


def unregister_webhook(webhook_id: str) -> bool:
    """注销Webhook（便捷函数）"""
    return get_webhook_manager().unregister_webhook(webhook_id)


def trigger_webhook(event_type: str, payload: Dict[str, Any]) -> Optional[Any]:
    """触发Webhook（便捷函数）"""
    return get_webhook_manager().queue_delivery(event_type, payload)


# ============ 与EventBus集成 ============

def setup_event_bus_integration():
    """设置EventBus集成"""
    try:
        from core.events import get_event_bus

        manager = get_webhook_manager()

        def on_event(event):
            manager.queue_delivery(event.type.value, event.data)

        event_bus = get_event_bus()
        event_bus.subscribe(on_event)
        logger.info("Webhook-EventBus integration enabled")
    except Exception as e:
        logger.error(f"Failed to setup EventBus integration: {e}")


# ============ 使用示例 ============
"""
【基本用法】

from core.webhook import (
    get_webhook_manager, register_webhook, trigger_webhook
)

# 注册Webhook
webhook_id = register_webhook(
    url="https://example.com/webhook",
    events={"agent_task_complete", "agent_task_error"},
    secret="my-secret-key",
    description="生产环境通知"
)

# 触发Webhook
trigger_webhook("agent_task_complete", {
    "agent": "dev_agent",
    "task_id": "task-001",
    "result": "success"
})

【与EventBus集成】

from core.webhook import setup_event_bus_integration

# 开启后，所有Agent事件会自动发送到已注册的Webhook
setup_event_bus_integration()

【验证签名】

from core.webhook import WebhookManager

manager = WebhookManager()
# 客户端验证:
payload = request.body
signature = request.headers['X-Webhook-Signature']
expected = manager._generate_signature(payload, secret)
if not hmac.compare_digest(signature, f"sha256={expected}"):
    # 签名不匹配，拒绝请求
"""


if __name__ == "__main__":
    print("Testing WebhookSystem...")

    manager = get_webhook_manager()

    # 注册测试Webhook
    wid = manager.register_webhook(
        url="https://httpbin.org/post",
        events={"agent_task_start", "agent_task_complete"},
        description="Test webhook"
    )
    print(f"Registered: {wid}")

    # 触发测试
    delivery_id = manager.queue_delivery("agent_task_start", {
        "agent": "test_agent",
        "task": "test"
    })
    print(f"Delivery queued: {delivery_id}")

    time.sleep(2)  # 等待投递

    if delivery_id:
        status = manager.get_delivery_status(delivery_id)
        print(f"Status: {status}")

    manager.shutdown()
    print("\nWebhookSystem OK")
