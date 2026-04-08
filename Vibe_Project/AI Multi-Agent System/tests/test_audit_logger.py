"""
测试审计日志系统

验证审计事件记录、查询、统计功能
"""

import pytest
import json
import time
from pathlib import Path
from logs.audit_logger import (
    AuditLogger,
    AuditEventType,
    get_audit_logger
)


class TestAuditLogger:
    """审计日志测试"""

    @pytest.fixture
    def audit(self):
        """创建独立的审计日志器用于测试"""
        logger = AuditLogger.__new__(AuditLogger)
        logger._log_dir = Path("G:/claude_code_project/logs/audit_test")
        logger._log_dir.mkdir(parents=True, exist_ok=True)
        logger._file_lock = __import__('threading').Lock()
        logger._initialized = True
        logger._counter = 0
        logger._counter_lock = __import__('threading').Lock()
        return logger

    def test_log_basic_event(self, audit):
        """记录基本事件"""
        event_id = audit.log(
            event_type=AuditEventType.API_REQUEST,
            user_id="test_user",
            endpoint="/api/test",
            method="GET"
        )
        assert event_id.startswith("AUDIT-")
        assert len(event_id) > 15

    def test_log_auth_success(self, audit):
        """记录认证成功"""
        event_id = audit.log_auth_success(
            user_id="user1",
            ip_address="192.168.1.1",
            method="jwt"
        )
        assert event_id.startswith("AUDIT-")

    def test_log_auth_failure(self, audit):
        """记录认证失败"""
        event_id = audit.log_auth_failure(
            user_id="unknown",
            ip_address="192.168.1.1",
            reason="invalid_token"
        )
        assert event_id.startswith("AUDIT-")

    def test_log_guardrail_block(self, audit):
        """记录Guardrails拦截"""
        event_id = audit.log_guardrail_block(
            user_id="user1",
            content_preview="<script>alert(1)</script>",
            reason="xss_attempt",
            ip_address="10.0.0.1"
        )
        assert event_id.startswith("AUDIT-")

    def test_log_guardrail_warn(self, audit):
        """记录Guardrails警告"""
        event_id = audit.log_guardrail_warn(
            user_id="user1",
            content_preview="Suspicious pattern detected",
            warning_type="suspicious_input",
            ip_address="10.0.0.1"
        )
        assert event_id.startswith("AUDIT-")

    def test_log_rate_limit_exceeded(self, audit):
        """记录限流触发"""
        event_id = audit.log_rate_limit_exceeded(
            user_id="user1",
            ip_address="192.168.1.100",
            limit_type="minute",
            endpoint="/api/chat"
        )
        assert event_id.startswith("AUDIT-")

    def test_log_session_created(self, audit):
        """记录会话创建"""
        event_id = audit.log_session_created(
            user_id="user1",
            session_id="session-123",
            ip_address="192.168.1.1"
        )
        assert event_id.startswith("AUDIT-")

    def test_log_session_deleted(self, audit):
        """记录会话删除"""
        event_id = audit.log_session_deleted(
            user_id="user1",
            session_id="session-123",
            ip_address="192.168.1.1"
        )
        assert event_id.startswith("AUDIT-")

    def test_event_id_uniqueness(self, audit):
        """事件ID唯一性"""
        ids = set()
        for _ in range(10):
            event_id = audit.log(
                event_type=AuditEventType.API_REQUEST,
                user_id="test"
            )
            ids.add(event_id)

        # 所有ID应该唯一
        assert len(ids) == 10

    def test_get_stats(self, audit):
        """获取统计"""
        # 记录多种事件
        audit.log_auth_success(user_id="u1", ip_address="1.1.1.1")
        audit.log_auth_failure(user_id="u2", ip_address="2.2.2.2")
        audit.log_guardrail_block(user_id="u3", content_preview="x", reason="y")

        stats = audit.get_stats()
        # 由于使用单例，可能有额外事件，只验证计数增加
        assert stats["auth_success"] >= 1
        assert stats["auth_failure"] >= 1
        assert stats["guardrail_block"] >= 1

    def test_get_recent_events_filtered(self, audit):
        """过滤查询事件"""
        unique_user = f"test_user_{int(time.time() * 1000) % 100000}"
        audit.log_auth_success(user_id=unique_user, ip_address="1.1.1.1")
        audit.log_auth_failure(user_id="other_user", ip_address="2.2.2.2")
        audit.log_api_request(user_id="another_user", endpoint="/api", method="GET", status_code=200)

        # 按用户过滤 - 应该至少找到我们创建的唯一用户
        user_events = audit.get_recent_events(user_id=unique_user)
        assert len(user_events) >= 1
        assert all(e["user_id"] == unique_user for e in user_events)

        # 按事件类型过滤 - 应该至少找到auth_success
        auth_events = audit.get_recent_events(event_type=AuditEventType.AUTH_SUCCESS)
        assert len(auth_events) >= 1
        assert all(e["event_type"] == "auth_success" for e in auth_events)


class TestAuditEventTypes:
    """审计事件类型测试"""

    def test_all_event_types_defined(self):
        """所有事件类型已定义"""
        expected_types = [
            "auth_success", "auth_failure", "auth_token_expired",
            "guardrail_block", "guardrail_warn", "rate_limit_exceeded",
            "input_sanitized", "session_created", "session_deleted",
            "session_accessed", "admin_action", "api_key_used", "api_request"
        ]
        actual_types = [e.value for e in AuditEventType]
        for expected in expected_types:
            assert expected in actual_types, f"Missing event type: {expected}"


class TestAuditLoggerSingleton:
    """单例测试"""

    def test_get_audit_logger_returns_same_instance(self):
        """获取同一实例"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2
