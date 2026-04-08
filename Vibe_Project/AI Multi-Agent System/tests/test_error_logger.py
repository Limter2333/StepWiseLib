"""
测试错误日志模块
"""

import pytest
import json
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestErrorLogger:
    """ErrorLogger测试"""

    def setup_method(self):
        """每个测试前创建临时日志目录"""
        self.temp_dir = tempfile.mkdtemp()
        # 直接使用已导出的error_logger实例
        from logs.error_logs import error_logger
        from pathlib import Path
        error_logger.log_dir = Path(self.temp_dir)
        error_logger.error_log_file = error_logger.log_dir / "error_test.json"

    def test_log_error(self):
        """测试记录错误"""
        from logs.error_logs import error_logger, ErrorLevel

        error_id = error_logger.log(
            error_type="TestError",
            message="This is a test error",
            level=ErrorLevel.ERROR
        )

        assert error_id is not None
        assert error_id.startswith("ERR-")

    def test_log_with_context(self):
        """测试带上下文的日志"""
        from logs.error_logs import error_logger, ErrorLevel

        error_id = error_logger.log(
            error_type="ContextError",
            message="Error with context",
            level=ErrorLevel.ERROR,
            context={"user_id": "123", "action": "test"}
        )

        assert error_id is not None

        # 验证记录的内容
        recent = error_logger.get_recent_errors(limit=1)
        if recent:
            assert "user_id" in recent[0].get("context", {})

    def test_log_with_exception(self):
        """测试带异常的日志"""
        from logs.error_logs import error_logger, ErrorLevel

        try:
            raise ValueError("Test exception")
        except ValueError as e:
            error_id = error_logger.log(
                error_type="ExceptionError",
                message="Caught an exception",
                level=ErrorLevel.ERROR,
                exc_info=e
            )

        assert error_id is not None

    def test_get_recent_errors(self):
        """测试获取最近错误"""
        from logs.error_logs import error_logger, ErrorLevel

        # 记录多条错误
        for i in range(5):
            error_logger.log(
                error_type=f"Error{i}",
                message=f"Error message {i}",
                level=ErrorLevel.ERROR
            )

        recent = error_logger.get_recent_errors(limit=3)
        assert len(recent) <= 3

    def test_get_recent_errors_by_level(self):
        """测试按级别过滤"""
        from logs.error_logs import error_logger, ErrorLevel

        error_logger.log("CriticalErr", "Critical", level=ErrorLevel.CRITICAL)
        error_logger.log("NormalErr", "Normal", level=ErrorLevel.ERROR)

        critical_errors = error_logger.get_recent_errors(
            limit=10,
            level=ErrorLevel.CRITICAL
        )

        for err in critical_errors:
            assert err.get("level") == "CRITICAL"

    def test_generate_report(self):
        """测试生成报告"""
        from logs.error_logs import error_logger

        # 添加一些测试错误
        for i in range(3):
            error_logger.log(
                error_type=f"TestError{i}",
                message=f"Test {i}"
            )

        report = error_logger.generate_error_report()

        assert "# 错误报告" in report or "error" in report.lower()
        assert "total" in report.lower() or "错误数" in report

    def test_error_levels(self):
        """测试错误级别"""
        from logs.error_logs import ErrorLevel

        assert ErrorLevel.CRITICAL.value == "CRITICAL"
        assert ErrorLevel.ERROR.value == "ERROR"
        assert ErrorLevel.WARNING.value == "WARNING"
        assert ErrorLevel.INFO.value == "INFO"

    def test_error_with_unicode(self):
        """测试Unicode字符处理"""
        from logs.error_logs import error_logger, ErrorLevel

        error_id = error_logger.log(
            error_type="UnicodeError",
            message="错误消息测试 🔥",
            level=ErrorLevel.ERROR
        )

        assert error_id is not None
        recent = error_logger.get_recent_errors(limit=1)
        if recent:
            assert "🔥" in recent[0].get("message", "")

    def test_error_with_empty_message(self):
        """测试空消息处理"""
        from logs.error_logs import error_logger, ErrorLevel

        error_id = error_logger.log(
            error_type="EmptyError",
            message="",
            level=ErrorLevel.ERROR
        )

        assert error_id is not None

    def test_error_with_long_message(self):
        """测试长消息处理"""
        from logs.error_logs import error_logger, ErrorLevel

        long_message = "A" * 10000
        error_id = error_logger.log(
            error_type="LongError",
            message=long_message,
            level=ErrorLevel.ERROR
        )

        assert error_id is not None

    def test_error_with_null_context(self):
        """测试None上下文处理"""
        from logs.error_logs import error_logger, ErrorLevel

        error_id = error_logger.log(
            error_type="NullContextError",
            message="Test",
            level=ErrorLevel.ERROR,
            context=None
        )

        assert error_id is not None

    def test_error_id_format(self):
        """测试错误ID格式"""
        from logs.error_logs import error_logger, ErrorLevel

        error_id = error_logger.log(
            error_type="FormatError",
            message="Test",
            level=ErrorLevel.ERROR
        )

        # 验证格式为 ERR-时间戳
        assert error_id.startswith("ERR-")
        parts = error_id.split("-")
        assert len(parts) >= 2

    def test_get_errors_with_zero_limit(self):
        """测试limit为0的情况（返回所有或空）"""
        from logs.error_logs import error_logger, ErrorLevel

        error_logger.log("ZeroLimitError", "Test", level=ErrorLevel.ERROR)
        errors = error_logger.get_recent_errors(limit=0)

        # limit=0时返回所有记录（因为-0等于0）
        assert isinstance(errors, list)

    def test_get_errors_with_large_limit(self):
        """测试limit大于实际错误数"""
        from logs.error_logs import error_logger, ErrorLevel

        error_logger.log("LargeLimitError", "Test", level=ErrorLevel.ERROR)
        errors = error_logger.get_recent_errors(limit=1000)

        assert isinstance(errors, list)
        assert len(errors) >= 1

    def test_error_count_tracking(self):
        """测试错误计数追踪"""
        from logs.error_logs import error_logger, ErrorLevel

        count_before = len(error_logger.get_recent_errors(limit=1000))
        error_logger.log("CountError", "Test", level=ErrorLevel.ERROR)
        count_after = len(error_logger.get_recent_errors(limit=1000))

        assert count_after > count_before


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
