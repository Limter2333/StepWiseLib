"""
测试Webhook系统
"""

import pytest
import time
import asyncio
from unittest.mock import patch, AsyncMock
from core.webhook import (
    WebhookManager,
    Webhook,
    WebhookDelivery,
    DeliveryStatus,
    get_webhook_manager,
    register_webhook,
    unregister_webhook,
    trigger_webhook,
)


@pytest.fixture
def manager():
    """创建测试用Webhook管理器"""
    m = WebhookManager()
    m._shutdown = False
    yield m
    m.shutdown()


class TestWebhookManager:
    """WebhookManager测试"""

    def test_register_webhook(self, manager):
        """注册Webhook"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"agent_task_start", "agent_task_complete"},
            description="Test"
        )

        assert webhook_id is not None
        webhook = manager.get_webhook(webhook_id)
        assert webhook is not None
        assert webhook.url == "https://example.com/webhook"
        assert "agent_task_start" in webhook.events

    def test_register_with_secret(self, manager):
        """注册带签名的Webhook"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"test"},
            secret="my-secret"
        )

        webhook = manager.get_webhook(webhook_id)
        assert webhook.secret == "my-secret"

    def test_unregister_webhook(self, manager):
        """注销Webhook"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"test"}
        )

        assert manager.unregister_webhook(webhook_id) is True
        assert manager.get_webhook(webhook_id) is None

    def test_unregister_nonexistent(self, manager):
        """注销不存在的Webhook"""
        assert manager.unregister_webhook("nonexistent") is False

    def test_list_webhooks(self, manager):
        """列出所有Webhook"""
        manager.register_webhook(
            url="https://example1.com/webhook",
            events={"event1"}
        )
        manager.register_webhook(
            url="https://example2.com/webhook",
            events={"event2"}
        )

        webhooks = manager.list_webhooks()
        assert len(webhooks) == 2

    def test_update_webhook(self, manager):
        """更新Webhook"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"test"}
        )

        assert manager.update_webhook(webhook_id, enabled=False) is True
        webhook = manager.get_webhook(webhook_id)
        assert webhook.enabled is False

    def test_queue_delivery_matching(self, manager):
        """队列投递 - 有匹配的Webhook"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"agent_task_start"}
        )

        delivery_id = manager.queue_delivery("agent_task_start", {"test": "data"})

        assert delivery_id is not None
        status = manager.get_delivery_status(delivery_id)
        assert status is not None
        assert status["status"] == "pending"

    def test_queue_delivery_no_matching(self, manager):
        """队列投递 - 无匹配的Webhook"""
        manager.register_webhook(
            url="https://example.com/webhook",
            events={"other_event"}
        )

        delivery_id = manager.queue_delivery("agent_task_start", {"test": "data"})

        assert delivery_id is None

    def test_queue_delivery_disabled_webhook(self, manager):
        """队列投递 - Webhook已禁用"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"agent_task_start"}
        )
        # 先禁用
        manager.update_webhook(webhook_id, enabled=False)

        delivery_id = manager.queue_delivery("agent_task_start", {"test": "data"})

        assert delivery_id is None

    def test_multiple_webhooks_same_event(self, manager):
        """多个Webhook订阅同一事件"""
        manager.register_webhook(
            url="https://example1.com/webhook",
            events={"agent_task_start"}
        )
        manager.register_webhook(
            url="https://example2.com/webhook",
            events={"agent_task_start"}
        )

        result = manager.queue_delivery("agent_task_start", {"test": "data"})

        # 返回列表
        assert isinstance(result, list)
        assert len(result) == 2

    def test_delivery_status(self, manager):
        """获取投递状态"""
        webhook_id = manager.register_webhook(
            url="https://example.com/webhook",
            events={"test"}
        )

        delivery_id = manager.queue_delivery("test", {})

        status = manager.get_delivery_status(delivery_id)
        assert status["webhook_id"] == webhook_id
        assert status["event_type"] == "test"
        assert status["attempts"] == 0

    def test_delivery_status_not_found(self, manager):
        """获取不存在的投递状态"""
        assert manager.get_delivery_status("nonexistent") is None


class TestWebhook:
    """Webhook数据类测试"""

    def test_webhook_creation(self):
        """创建Webhook"""
        webhook = Webhook(
            id="test-123",
            url="https://example.com",
            events={"event1", "event2"},
            secret="secret",
            description="Test webhook"
        )

        assert webhook.id == "test-123"
        assert webhook.url == "https://example.com"
        assert len(webhook.events) == 2
        assert webhook.enabled is True


class TestWebhookDelivery:
    """WebhookDelivery数据类测试"""

    def test_delivery_creation(self):
        """创建投递"""
        delivery = WebhookDelivery(
            delivery_id="del-123",
            webhook_id="webhook-123",
            event_type="agent_task_start",
            payload={"test": "data"},
            status=DeliveryStatus.PENDING
        )

        assert delivery.delivery_id == "del-123"
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.attempts == 0

    def test_delivery_retry_count(self):
        """投递重试计数"""
        delivery = WebhookDelivery(
            delivery_id="del-123",
            webhook_id="webhook-123",
            event_type="test",
            payload={},
            status=DeliveryStatus.PENDING,
            max_attempts=3
        )

        assert delivery.attempts < delivery.max_attempts
        delivery.attempts = 2
        assert delivery.attempts < delivery.max_attempts
        delivery.attempts = 3
        assert delivery.attempts >= delivery.max_attempts


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_webhook_manager_singleton(self):
        """单例模式"""
        m1 = get_webhook_manager()
        m2 = get_webhook_manager()
        assert m1 is m2

    def test_register_and_trigger(self):
        """注册并触发"""
        # 这个测试需要mock
        pass


class TestSignature:
    """签名测试"""

    def test_generate_signature(self, manager):
        """生成签名"""
        payload = '{"test": "data"}'
        secret = "my-secret"

        signature = manager._generate_signature(payload, secret)

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex

    def test_signature_consistency(self, manager):
        """签名一致性"""
        payload = '{"test": "data"}'
        secret = "my-secret"

        sig1 = manager._generate_signature(payload, secret)
        sig2 = manager._generate_signature(payload, secret)

        assert sig1 == sig2

    def test_signature_different_secrets(self, manager):
        """不同密钥生成不同签名"""
        payload = '{"test": "data"}'

        sig1 = manager._generate_signature(payload, "secret1")
        sig2 = manager._generate_signature(payload, "secret2")

        assert sig1 != sig2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
