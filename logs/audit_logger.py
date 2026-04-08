"""
审计日志系统
============

【功能】
1. 记录所有安全相关事件
2. 可搜索的JSON格式日志
3. 自动按日期分文件
4. 线程安全

【记录的事件类型】
- 认证成功/失败
- Guardrails拦截/警告
- 限流触发
- 输入清洗
- 会话创建/删除
- 管理员操作

【使用场景】
- 安全审计追踪
- 合规报告（SOC2/GDPR）
- 异常行为检测
- 事件调查
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import threading
from pathlib import Path


class AuditEventType(Enum):
    """审计事件类型"""
    # 认证事件
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"

    # 安全事件
    GUARDRAIL_BLOCK = "guardrail_block"
    GUARDRAIL_WARN = "guardrail_warn"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INPUT_SANITIZED = "input_sanitized"

    # 会话事件
    SESSION_CREATED = "session_created"
    SESSION_DELETED = "session_deleted"
    SESSION_ACCESSED = "session_accessed"

    # 管理员操作
    ADMIN_ACTION = "admin_action"

    # API使用
    API_KEY_USED = "api_key_used"
    API_REQUEST = "api_request"


@dataclass
class AuditRecord:
    """审计记录"""
    event_id: str
    timestamp: str
    event_type: str
    user_id: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    risk_level: str = "LOW"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "risk_level": self.risk_level,
            "details": self.details
        }


class AuditLogger:
    """审计日志器

    线程安全的JSON审计日志系统
    自动按日期分文件存储
    """

    _instance: Optional['AuditLogger'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'AuditLogger':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._log_dir = Path("G:/claude_code_project/logs/audit")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._file_lock = threading.Lock()
        self._initialized = True

        # 事件计数器（用于生成ID）
        self._counter = 0
        self._counter_lock = threading.Lock()

    def _generate_event_id(self) -> str:
        """生成唯一事件ID"""
        with self._counter_lock:
            self._counter += 1
            return f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"

    def _get_log_file(self) -> Path:
        """获取当天的日志文件"""
        return self._log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

    def _write_record(self, record: AuditRecord):
        """写入单条记录"""
        with self._file_lock:
            log_file = self._get_log_file()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def log(
        self,
        event_type: AuditEventType,
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        risk_level: str = "LOW",
        **details
    ) -> str:
        """记录审计事件

        Args:
            event_type: 事件类型
            user_id: 用户ID
            session_id: 会话ID
            ip_address: IP地址
            user_agent: 用户代理
            risk_level: 风险等级 (LOW/MEDIUM/HIGH/CRITICAL)
            **details: 其他详细信息

        Returns:
            事件ID
        """
        record = AuditRecord(
            event_id=self._generate_event_id(),
            timestamp=datetime.now().isoformat(),
            event_type=event_type.value,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            risk_level=risk_level,
            details=details
        )

        self._write_record(record)
        return record.event_id

    def log_auth_success(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        method: str = "jwt"
    ):
        """记录认证成功"""
        return self.log(
            event_type=AuditEventType.AUTH_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            risk_level="LOW",
            method=method
        )

    def log_auth_failure(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        reason: str = "invalid_token"
    ):
        """记录认证失败"""
        return self.log(
            event_type=AuditEventType.AUTH_FAILURE,
            user_id=user_id,
            ip_address=ip_address,
            risk_level="HIGH",
            reason=reason
        )

    def log_guardrail_block(
        self,
        user_id: str,
        content_preview: str,
        reason: str,
        ip_address: Optional[str] = None
    ):
        """记录Guardrails拦截"""
        return self.log(
            event_type=AuditEventType.GUARDRAIL_BLOCK,
            user_id=user_id,
            ip_address=ip_address,
            risk_level="MEDIUM",
            content_preview=content_preview[:200],
            reason=reason
        )

    def log_guardrail_warn(
        self,
        user_id: str,
        content_preview: str,
        warning_type: str,
        ip_address: Optional[str] = None
    ):
        """记录Guardrails警告"""
        return self.log(
            event_type=AuditEventType.GUARDRAIL_WARN,
            user_id=user_id,
            ip_address=ip_address,
            risk_level="LOW",
            content_preview=content_preview[:200],
            warning_type=warning_type
        )

    def log_rate_limit_exceeded(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        limit_type: str = "minute",
        endpoint: str = ""
    ):
        """记录限流触发"""
        return self.log(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            ip_address=ip_address,
            risk_level="MEDIUM",
            limit_type=limit_type,
            endpoint=endpoint
        )

    def log_session_created(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None
    ):
        """记录会话创建"""
        return self.log(
            event_type=AuditEventType.SESSION_CREATED,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            risk_level="LOW"
        )

    def log_session_deleted(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None
    ):
        """记录会话删除"""
        return self.log(
            event_type=AuditEventType.SESSION_DELETED,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            risk_level="MEDIUM"
        )

    def log_api_request(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """记录API请求"""
        risk = "LOW"
        if status_code >= 500:
            risk = "HIGH"
        elif status_code >= 400:
            risk = "MEDIUM"

        return self.log(
            event_type=AuditEventType.API_REQUEST,
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            risk_level=risk,
            endpoint=endpoint,
            method=method,
            status_code=status_code
        )

    def get_recent_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """获取最近的审计事件"""
        log_file = self._get_log_file()
        if not log_file.exists():
            return []

        events = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    # 过滤
                    if event_type and record.get('event_type') != event_type.value:
                        continue
                    if user_id and record.get('user_id') != user_id:
                        continue
                    events.append(record)
                    if len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue

        return events

    def get_stats(self) -> Dict[str, int]:
        """获取审计统计"""
        stats = {e.value: 0 for e in AuditEventType}
        log_file = self._get_log_file()

        if not log_file.exists():
            return stats

        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    event_type = record.get('event_type', '')
                    if event_type in stats:
                        stats[event_type] += 1
                except json.JSONDecodeError:
                    continue

        return stats


# ========== 全局实例 ==========

_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取审计日志器单例"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# ========== 使用示例 ==========
"""
from logs.audit_logger import get_audit_logger, AuditEventType

audit = get_audit_logger()

# 记录认证
audit.log_auth_success(user_id="user123", ip_address="192.168.1.1")

# 记录Guardrails拦截
audit.log_guardrail_block(
    user_id="user123",
    content_preview="malicious input...",
    reason="prompt_injection"
)

# 记录API请求
audit.log_api_request(
    user_id="user123",
    endpoint="/api/chat/completions",
    method="POST",
    status_code=200
)

# 查询统计
stats = audit.get_stats()
print(f"Auth failures: {stats['auth_failure']}")

# 获取最近的安全事件
recent_blocks = audit.get_recent_events(event_type=AuditEventType.GUARDRAIL_BLOCK, limit=10)
"""


if __name__ == "__main__":
    # 快速测试
    audit = get_audit_logger()

    print("Testing audit logger...")

    # 测试基本日志
    event_id = audit.log(
        event_type=AuditEventType.API_REQUEST,
        user_id="test_user",
        ip_address="127.0.0.1",
        endpoint="/api/test",
        method="GET"
    )
    print(f"Logged event: {event_id}")

    # 测试快捷方法
    audit.log_auth_success(user_id="user1", ip_address="192.168.1.1")
    audit.log_guardrail_block(user_id="user2", content_preview="test content", reason="xss_attempt")

    # 获取统计
    stats = audit.get_stats()
    print(f"Audit stats: {stats}")

    print("\\nAuditLogger OK")
