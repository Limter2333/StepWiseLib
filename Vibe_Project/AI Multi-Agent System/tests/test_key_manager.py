"""
测试密钥管理系统
"""

import pytest
import time
from core.key_manager import (
    SecretStore,
    Key,
    KeyType,
    KeyStatus,
    StoredKey,
    get_secret_store,
    store_secret,
    get_secret,
)


@pytest.fixture
def store():
    """创建测试用密钥存储"""
    s = SecretStore(master_key="test-master-key-12345")
    yield s


class TestSecretStore:
    """SecretStore测试"""

    def test_store_and_retrieve(self, store):
        """存储和获取密钥"""
        key_id = store.store(
            name="test_key",
            value="secret_value",
            key_type=KeyType.SECRET_KEY,
            client_id="test"
        )

        assert key_id is not None

        value = store.retrieve("test_key", client_id="test")
        assert value == "secret_value"

    def test_store_duplicate_name(self, store):
        """存储重复名称应失败"""
        store.store("test_key", "value1", KeyType.SECRET_KEY, client_id="test")

        with pytest.raises(ValueError, match="already exists"):
            store.store("test_key", "value2", KeyType.SECRET_KEY, client_id="test")

    def test_retrieve_nonexistent(self, store):
        """获取不存在的密钥"""
        with pytest.raises(KeyError):
            store.retrieve("nonexistent", client_id="test")

    def test_get_info(self, store):
        """获取密钥信息"""
        store.store(
            name="test_key",
            value="secret",
            key_type=KeyType.API_KEY,
            client_id="test",
            metadata={"env": "prod"}
        )

        info = store.get_info("test_key", client_id="test")

        assert info["name"] == "test_key"
        assert info["key_type"] == "api_key"
        assert info["status"] == "active"
        assert info["metadata"]["env"] == "prod"
        assert "encrypted_value" not in info  # 不应包含值

    def test_list_keys(self, store):
        """列出密钥"""
        store.store("key1", "v1", KeyType.API_KEY, client_id="client1")
        store.store("key2", "v2", KeyType.SECRET_KEY, client_id="client1")

        keys = store.list_keys(client_id="client1")

        assert len(keys) == 2
        names = {k["name"] for k in keys}
        assert "key1" in names
        assert "key2" in names

    def test_revoke(self, store):
        """撤销密钥"""
        store.store("test_key", "secret", KeyType.SECRET_KEY, client_id="test")

        assert store.revoke("test_key", client_id="admin") is True

        with pytest.raises(PermissionError, match="revoked"):
            store.retrieve("test_key", client_id="test")

    def test_suspend_and_restore(self, store):
        """暂停和恢复密钥"""
        store.store("test_key", "secret", KeyType.SECRET_KEY, client_id="test")

        assert store.suspend("test_key", client_id="admin") is True

        with pytest.raises(PermissionError, match="suspended"):
            store.retrieve("test_key", client_id="test")

        assert store.restore("test_key", client_id="admin") is True

        value = store.retrieve("test_key", client_id="test")
        assert value == "secret"

    def test_rotate(self, store):
        """轮换密钥"""
        store.store(
            "test_key",
            "old_value",
            KeyType.SECRET_KEY,
            client_id="test",
            rotation_days=30
        )

        assert store.rotate("test_key", "new_value", client_id="admin") is True

        value = store.retrieve("test_key", client_id="test")
        assert value == "new_value"

    def test_delete(self, store):
        """删除密钥"""
        store.store("test_key", "secret", KeyType.SECRET_KEY, client_id="test")

        assert store.delete("test_key", client_id="test") is True

        with pytest.raises(KeyError):
            store.retrieve("test_key", client_id="test")

    def test_audit_log(self, store):
        """审计日志"""
        store.store("key1", "v1", KeyType.API_KEY, client_id="test")
        store.retrieve("key1", client_id="test")

        log = store.get_audit_log(client_id="test")

        assert len(log) >= 2
        actions = {entry["action"] for entry in log}
        assert "store" in actions
        assert "retrieve" in actions

    def test_expired_key(self, store):
        """过期密钥"""
        store.store(
            "test_key",
            "secret",
            KeyType.SECRET_KEY,
            client_id="test",
            expires_at=time.time() - 1  # 已过期
        )

        with pytest.raises(PermissionError, match="expired"):
            store.retrieve("test_key", client_id="test")

    def test_use_count(self, store):
        """使用计数"""
        store.store("test_key", "secret", KeyType.SECRET_KEY, client_id="test")

        store.retrieve("test_key", client_id="test")
        store.retrieve("test_key", client_id="test")

        info = store.get_info("test_key", client_id="test")
        assert info["use_count"] == 2


class TestKeyTypes:
    """密钥类型测试"""

    def test_all_key_types(self):
        """所有密钥类型存在"""
        assert KeyType.API_KEY.value == "api_key"
        assert KeyType.SECRET_KEY.value == "secret_key"
        assert KeyType.ACCESS_TOKEN.value == "access_token"
        assert KeyType.REFRESH_TOKEN.value == "refresh_token"
        assert KeyType.DATABASE_PASSWORD.value == "database_password"
        assert KeyType.ENCRYPTION_KEY.value == "encryption_key"


class TestKeyStatus:
    """密钥状态测试"""

    def test_all_statuses(self):
        """所有密钥状态存在"""
        assert KeyStatus.ACTIVE.value == "active"
        assert KeyStatus.EXPIRED.value == "expired"
        assert KeyStatus.REVOKED.value == "revoked"
        assert KeyStatus.SUSPENDED.value == "suspended"


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_secret_store_singleton(self):
        """单例"""
        s1 = get_secret_store()
        s2 = get_secret_store()
        assert s1 is s2

    def test_store_and_get_secret(self):
        """存储和获取"""
        SecretStore._instance = None
        store = SecretStore()

        store_secret("test", "value", KeyType.SECRET_KEY, client_id="test")
        value = get_secret("test", client_id="test")

        assert value == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
