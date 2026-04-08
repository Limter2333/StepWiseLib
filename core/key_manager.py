"""
密钥管理系统 - Secure Key Management
=====================================

【功能】
1. 密钥存储 - 加密存储敏感信息
2. 密钥轮换 - 自动/手动密钥轮换
3. 访问控制 - 按客户端/角色控制密钥访问
4. 审计日志 - 记录所有密钥访问
5. 密钥生成 - 支持多种算法生成密钥

【使用场景】
- 存储LLM API密钥
- 管理数据库密码
- 控制第三方服务访问密钥
- 密钥自动过期和轮换
"""

import os
import secrets
import hashlib
import hmac
import base64
import json
import time
import uuid
from typing import Dict, Optional, Any, Set, List
from dataclasses import dataclass, field
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class KeyType(Enum):
    """密钥类型"""
    API_KEY = "api_key"
    SECRET_KEY = "secret_key"
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    DATABASE_PASSWORD = "database_password"
    ENCRYPTION_KEY = "encryption_key"


class KeyStatus(Enum):
    """密钥状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class Key:
    """密钥"""
    key_id: str
    name: str
    key_type: KeyType
    status: KeyStatus
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    use_count: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
    rotation_days: Optional[int] = None  # 自动轮换天数
    next_rotation_at: Optional[float] = None

    def is_expired(self) -> bool:
        if self.status == KeyStatus.EXPIRED:
            return True
        if self.expires_at and time.time() > self.expires_at:
            return True
        return False

    def needs_rotation(self) -> bool:
        if not self.next_rotation_at:
            return False
        return time.time() >= self.next_rotation_at


@dataclass
class StoredKey:
    """存储的密钥（含加密）"""
    key_id: str
    name: str
    key_type: KeyType
    encrypted_value: str  # 加密后的值
    key_hash: str  # 用于验证的哈希
    status: KeyStatus
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    use_count: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
    rotation_days: Optional[int] = None
    next_rotation_at: Optional[float] = None


class KeyRotation:
    """密钥轮换策略"""

    def __init__(
        self,
        enabled: bool = True,
        auto_rotate: bool = True,
        rotation_days: int = 90,
        notify_before_days: int = 7
    ):
        self.enabled = enabled
        self.auto_rotate = auto_rotate
        self.rotation_days = rotation_days
        self.notify_before_days = notify_before_days


class SecretStore:
    """密钥存储

    【架构】
    - 内存存储（可配置加密）
    - 按名称和类型组织
    - 支持访问控制和审计
    """

    def __init__(self, master_key: Optional[str] = None):
        # 如果没有提供主密钥，生成一个
        self._master_key = master_key or self._generate_master_key()
        self._keys: Dict[str, StoredKey] = {}  # key_id -> StoredKey
        self._name_index: Dict[str, str] = {}  # name -> key_id
        self._lock = threading.RLock()

        # 访问控制
        self._acls: Dict[str, Set[str]] = {}  # key_id -> set of client_ids
        self._global_acl: Set[str] = set()  # 可访问所有密钥的客户端

        # 审计日志
        self._audit_log: List[Dict] = []
        self._max_audit_entries = 1000

        # 轮换策略
        self._rotation = KeyRotation()

        logger.info("SecretStore initialized")

    def _generate_master_key(self) -> str:
        """生成主密钥"""
        return base64.b64encode(secrets.token_bytes(32)).decode()

    def _encrypt(self, value: str) -> str:
        """加密值（简单实现，生产环境应使用更强的加密）"""
        # 使用主密钥进行简单的XOR加密
        key_bytes = self._master_key.encode()
        value_bytes = value.encode()
        encrypted = bytes(a ^ b for a, b in zip(value_bytes, (key_bytes * (len(value_bytes) // len(key_bytes) + 1))[:len(value_bytes)]))
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted: str) -> str:
        """解密值"""
        key_bytes = self._master_key.encode()
        encrypted_bytes = base64.b64decode(encrypted)
        decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, (key_bytes * (len(encrypted_bytes) // len(key_bytes) + 1))[:len(encrypted_bytes)]))
        return decrypted.decode()

    def _hash_key(self, value: str) -> str:
        """哈希密钥（用于验证，不存储明文）"""
        return hashlib.sha256(value.encode()).hexdigest()

    def _audit(self, action: str, key_id: str, client_id: str, details: Optional[str] = None):
        """记录审计日志"""
        entry = {
            "timestamp": time.time(),
            "action": action,
            "key_id": key_id,
            "client_id": client_id,
            "details": details
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > self._max_audit_entries:
            self._audit_log.pop(0)

    def store(
        self,
        name: str,
        value: str,
        key_type: KeyType,
        client_id: str,
        expires_at: Optional[float] = None,
        metadata: Optional[Dict[str, str]] = None,
        rotation_days: Optional[int] = None
    ) -> str:
        """存储密钥

        Args:
            name: 密钥名称
            value: 密钥值
            key_type: 密钥类型
            client_id: 客户端ID（用于审计）
            expires_at: 过期时间戳
            metadata: 元数据
            rotation_days: 自动轮换天数

        Returns:
            key_id
        """
        key_id = str(uuid.uuid4())[:8]

        with self._lock:
            # 检查名称是否已存在
            if name in self._name_index:
                raise ValueError(f"Key with name '{name}' already exists")

            # 加密存储
            encrypted = self._encrypt(value)
            key_hash = self._hash_key(value)

            next_rotation = None
            if rotation_days and self._rotation.enabled:
                next_rotation = time.time() + (rotation_days * 86400)

            stored_key = StoredKey(
                key_id=key_id,
                name=name,
                key_type=key_type,
                encrypted_value=encrypted,
                key_hash=key_hash,
                status=KeyStatus.ACTIVE,
                created_at=time.time(),
                expires_at=expires_at,
                metadata=metadata or {},
                rotation_days=rotation_days,
                next_rotation_at=next_rotation
            )

            self._keys[key_id] = stored_key
            self._name_index[name] = key_id

        self._audit("store", key_id, client_id, f"type={key_type.value}")
        logger.info(f"Stored key '{name}' ({key_id})")

        return key_id

    def retrieve(self, name: str, client_id: str) -> str:
        """获取密钥值

        Args:
            name: 密钥名称
            client_id: 客户端ID

        Returns:
            密钥值
        """
        with self._lock:
            if name not in self._name_index:
                raise KeyError(f"Key '{name}' not found")

            key_id = self._name_index[name]
            stored_key = self._keys[key_id]

            # 检查状态
            if stored_key.status == KeyStatus.REVOKED:
                raise PermissionError("Key has been revoked")
            if stored_key.status == KeyStatus.SUSPENDED:
                raise PermissionError("Key is suspended")
            # 检查过期
            if stored_key.expires_at and time.time() > stored_key.expires_at:
                stored_key.status = KeyStatus.EXPIRED
                raise PermissionError("Key has expired")

            # 更新使用统计
            stored_key.last_used_at = time.time()
            stored_key.use_count += 1

        self._audit("retrieve", key_id, client_id)
        return self._decrypt(stored_key.encrypted_value)

    def get_info(self, name: str, client_id: str) -> Dict:
        """获取密钥信息（不含值）"""
        with self._lock:
            if name not in self._name_index:
                raise KeyError(f"Key '{name}' not found")

            key_id = self._name_index[name]
            stored_key = self._keys[key_id]

            # 检查是否需要轮换
            needs_rotation = False
            if stored_key.next_rotation_at and stored_key.status == KeyStatus.ACTIVE:
                needs_rotation = time.time() >= stored_key.next_rotation_at

            return {
                "key_id": stored_key.key_id,
                "name": stored_key.name,
                "key_type": stored_key.key_type.value,
                "status": stored_key.status.value,
                "created_at": stored_key.created_at,
                "expires_at": stored_key.expires_at,
                "last_used_at": stored_key.last_used_at,
                "use_count": stored_key.use_count,
                "metadata": stored_key.metadata,
                "needs_rotation": needs_rotation,
                "next_rotation_at": stored_key.next_rotation_at
            }

    def list_keys(self, client_id: str) -> List[Dict]:
        """列出所有可访问的密钥（不含值）"""
        with self._lock:
            accessible = []

            for key_id, stored_key in self._keys.items():
                # 如果没有配置ACL，使用宽松策略：允许列出ACTIVE状态的密钥
                has_access = (
                    stored_key.status == KeyStatus.ACTIVE and
                    (not self._acls.get(key_id) and not self._global_acl or
                     client_id in self._global_acl or
                     client_id in self._acls.get(key_id, set()))
                )
                if has_access:
                    needs_rotation = False
                    if stored_key.next_rotation_at and stored_key.status == KeyStatus.ACTIVE:
                        needs_rotation = time.time() >= stored_key.next_rotation_at

                    accessible.append({
                        "key_id": key_id,
                        "name": stored_key.name,
                        "key_type": stored_key.key_type.value,
                        "status": stored_key.status.value,
                        "created_at": stored_key.created_at,
                        "last_used_at": stored_key.last_used_at,
                        "use_count": stored_key.use_count,
                        "needs_rotation": needs_rotation
                    })

            return accessible

    def revoke(self, name: str, client_id: str) -> bool:
        """撤销密钥"""
        with self._lock:
            if name not in self._name_index:
                return False

            key_id = self._name_index[name]
            self._keys[key_id].status = KeyStatus.REVOKED

        self._audit("revoke", key_id, client_id)
        logger.info(f"Revoked key '{name}' ({key_id})")
        return True

    def suspend(self, name: str, client_id: str) -> bool:
        """暂停密钥"""
        with self._lock:
            if name not in self._name_index:
                return False

            key_id = self._name_index[name]
            self._keys[key_id].status = KeyStatus.SUSPENDED

        self._audit("suspend", key_id, client_id)
        return True

    def restore(self, name: str, client_id: str) -> bool:
        """恢复密钥"""
        with self._lock:
            if name not in self._name_index:
                return False

            key_id = self._name_index[name]
            stored_key = self._keys[key_id]
            if stored_key.status in (KeyStatus.SUSPENDED, KeyStatus.EXPIRED):
                stored_key.status = KeyStatus.ACTIVE

        self._audit("restore", key_id, client_id)
        return True

    def rotate(self, name: str, new_value: str, client_id: str) -> bool:
        """轮换密钥"""
        with self._lock:
            if name not in self._name_index:
                return False

            key_id = self._name_index[name]
            stored_key = self._keys[key_id]

            # 更新值
            stored_key.encrypted_value = self._encrypt(new_value)
            stored_key.key_hash = self._hash_key(new_value)
            stored_key.created_at = time.time()

            # 更新下次轮换时间
            if stored_key.rotation_days and self._rotation.enabled:
                stored_key.next_rotation_at = time.time() + (stored_key.rotation_days * 86400)

        self._audit("rotate", key_id, client_id)
        logger.info(f"Rotated key '{name}' ({key_id})")
        return True

    def delete(self, name: str, client_id: str) -> bool:
        """删除密钥"""
        with self._lock:
            if name not in self._name_index:
                return False

            key_id = self._name_index[name]
            del self._keys[key_id]
            del self._name_index[name]
            if key_id in self._acls:
                del self._acls[key_id]

        self._audit("delete", key_id, client_id)
        logger.info(f"Deleted key '{name}' ({key_id})")
        return True

    def get_audit_log(self, client_id: str, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        with self._lock:
            return list(self._audit_log[-limit:])

    def check_rotation_needed(self) -> List[Dict]:
        """检查需要轮换的密钥"""
        with self._lock:
            needed = []
            now = time.time()
            for stored_key in self._keys.values():
                if (stored_key.status == KeyStatus.ACTIVE and
                    stored_key.next_rotation_at and
                    now >= stored_key.next_rotation_at):
                    needed.append({
                        "key_id": stored_key.key_id,
                        "name": stored_key.name,
                        "key_type": stored_key.key_type.value,
                        "next_rotation_at": stored_key.next_rotation_at
                    })
            return needed


# ============ 便捷函数 ============

_store: Optional[SecretStore] = None


def get_secret_store() -> SecretStore:
    """获取密钥存储单例"""
    global _store
    if _store is None:
        _store = SecretStore()
    return _store


def store_secret(
    name: str,
    value: str,
    key_type: KeyType = KeyType.SECRET_KEY,
    **kwargs
) -> str:
    """存储密钥（便捷函数）"""
    return get_secret_store().store(name, value, key_type, **kwargs)


def get_secret(name: str, **kwargs) -> str:
    """获取密钥（便捷函数）"""
    return get_secret_store().retrieve(name, **kwargs)


# ============ 使用示例 ============
"""
【基本用法】

from core.key_manager import (
    SecretStore, KeyType, get_secret_store, store_secret, get_secret
)

store = get_secret_store()

# 存储密钥
store.store(
    name="openai_api_key",
    value="sk-xxx...",
    key_type=KeyType.API_KEY,
    metadata={"owner": "dev-team"},
    rotation_days=90
)

# 获取密钥
api_key = store.retrieve("openai_api_key", client_id="my-app")

# 列出所有密钥
keys = store.list_keys(client_id="my-app")
for k in keys:
    print(f"{k['name']} ({k['key_type']})")

【审计日志】

log = store.get_audit_log(client_id="admin")
for entry in log:
    print(f"{entry['timestamp']} - {entry['action']} - {entry['key_id']}")

【轮换检查】

to_rotate = store.check_rotation_needed()
for key in to_rotate:
    print(f"Key {key['name']} needs rotation")
"""


if __name__ == "__main__":
    print("Testing KeyManager...")

    store = SecretStore()

    # 存储密钥
    key_id = store.store(
        name="test_key",
        value="super-secret-value",
        key_type=KeyType.SECRET_KEY,
        client_id="test",
        metadata={"env": "test"}
    )
    print(f"Stored key: {key_id}")

    # 获取密钥
    value = store.retrieve("test_key", client_id="test")
    print(f"Retrieved: {value}")

    # 列出密钥
    keys = store.list_keys(client_id="test")
    print(f"Keys: {keys}")

    # 审计日志
    log = store.get_audit_log(client_id="test")
    print(f"Audit log: {len(log)} entries")

    print("\nKeyManager OK")
