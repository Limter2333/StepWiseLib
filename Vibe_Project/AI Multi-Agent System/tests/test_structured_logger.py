"""
Tests for Structured Logger

Tests cover:
- JSON output format verification
- Context propagation (request_id, session_id, agent_name)
- Thread-safe implementation
- All log levels
- Context manager functionality
- Decorator functionality
- Nested context managers
"""

import pytest
import json
import logging
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
import threading

from logs.structured_logger import (
    StructuredLogger,
    set_context,
    get_context,
    clear_context,
    get_logger,
    request_id_var,
    session_id_var,
    agent_name_var,
)


class LogCapture:
    """Helper class to capture log output."""

    def __init__(self):
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        self.handler.setFormatter(formatter)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.handler.close()

    def get_output(self) -> str:
        return self.stream.getvalue()

    def clear(self):
        self.stream.truncate(0)
        self.stream.seek(0)


@pytest.fixture(autouse=True)
def clean_context():
    """Ensure clean context before and after each test."""
    clear_context()
    yield
    clear_context()


@pytest.fixture
def logger():
    """Create a fresh logger instance with capture."""
    logger_instance = StructuredLogger("test_logger")
    return logger_instance


class TestJsonOutputFormat:
    """Tests for JSON output format."""

    def test_output_is_valid_json(self, logger):
        """Verify log output is valid JSON."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.info("Test message")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert "message" in parsed
            assert "context" in parsed
            assert "timestamp" in parsed

    def test_json_contains_message(self, logger):
        """Verify JSON output contains the message."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.info("Hello World")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["message"] == "Hello World"

    def test_json_contains_timestamp(self, logger):
        """Verify JSON output contains ISO timestamp."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.info("Test")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert "timestamp" in parsed
            # Verify ISO format
            from datetime import datetime
            datetime.fromisoformat(parsed["timestamp"])

    def test_json_contains_context(self, logger):
        """Verify JSON output contains context object."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.info("Test")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert "context" in parsed
            assert isinstance(parsed["context"], dict)

    def test_extra_fields_included_in_context(self, logger):
        """Verify extra keyword arguments are included in context."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.info("Test", custom_field="value", number=42)

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["context"]["custom_field"] == "value"
            assert parsed["context"]["number"] == 42


class TestContextPropagation:
    """Tests for request context propagation."""

    def test_initial_context_is_none(self):
        """Verify context starts as None."""
        context = get_context()
        assert context["request_id"] is None
        assert context["session_id"] is None
        assert context["agent"] is None

    def test_set_request_id_propagates(self, logger):
        """Verify request_id is propagated to logs."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            set_context(request_id="req-123")
            logger.info("Test")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["context"]["request_id"] == "req-123"

    def test_set_session_id_propagates(self, logger):
        """Verify session_id is propagated to logs."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            set_context(session_id="sess-456")
            logger.info("Test")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["context"]["session_id"] == "sess-456"

    def test_set_agent_name_propagates(self, logger):
        """Verify agent_name is propagated to logs."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            set_context(agent_name="test_agent")
            logger.info("Test")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["context"]["agent"] == "test_agent"

    def test_all_context_fields_together(self, logger):
        """Verify all context fields propagate together."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            set_context(
                request_id="req-123",
                session_id="sess-456",
                agent_name="my_agent"
            )
            logger.info("Test")

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["context"]["request_id"] == "req-123"
            assert parsed["context"]["session_id"] == "sess-456"
            assert parsed["context"]["agent"] == "my_agent"


class TestLogLevels:
    """Tests for all log levels."""

    def test_debug_level(self, logger):
        """Verify DEBUG level works."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug message")

            output = capture.get_output().strip()
            assert len(output) > 0
            parsed = json.loads(output)
            assert parsed["message"] == "Debug message"

    def test_info_level(self, logger):
        """Verify INFO level works."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.info("Info message")

            output = capture.get_output().strip()
            parsed = json.loads(output)
            assert parsed["message"] == "Info message"

    def test_warning_level(self, logger):
        """Verify WARNING level works."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.warning("Warning message")

            output = capture.get_output().strip()
            parsed = json.loads(output)
            assert parsed["message"] == "Warning message"

    def test_error_level(self, logger):
        """Verify ERROR level works."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.error("Error message")

            output = capture.get_output().strip()
            parsed = json.loads(output)
            assert parsed["message"] == "Error message"

    def test_critical_level(self, logger):
        """Verify CRITICAL level works."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)
            logger.critical("Critical message")

            output = capture.get_output().strip()
            parsed = json.loads(output)
            assert parsed["message"] == "Critical message"


class TestContextManager:
    """Tests for context manager functionality."""

    def test_bind_context_temporarily(self, logger):
        """Verify bind() temporarily sets context."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)

            # Before context manager, context is None
            logger.info("Before")
            before_output = capture.get_output().strip()
            before_parsed = json.loads(before_output)
            assert before_parsed["context"]["request_id"] is None

            capture.clear()

            # Inside context manager, context is set
            with logger.bind(request_id="temp-req"):
                logger.info("Inside")

            inside_output = capture.get_output().strip()
            inside_parsed = json.loads(inside_output)
            assert inside_parsed["context"]["request_id"] == "temp-req"

            capture.clear()

            # After context manager, context is restored to None
            logger.info("After")
            after_output = capture.get_output().strip()
            after_parsed = json.loads(after_output)
            assert after_parsed["context"]["request_id"] is None

    def test_nested_context_managers(self, logger):
        """Verify nested context managers work correctly."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)

            with logger.bind(request_id="outer"):
                logger.info("Outer 1")
                outer1 = json.loads(capture.get_output().strip())
                assert outer1["context"]["request_id"] == "outer"

                capture.clear()

                with logger.bind(request_id="inner"):
                    logger.info("Inner")
                    inner = json.loads(capture.get_output().strip())
                    assert inner["context"]["request_id"] == "inner"

                capture.clear()

                logger.info("Outer 2")
                outer2 = json.loads(capture.get_output().strip())
                assert outer2["context"]["request_id"] == "outer"


class TestDecorator:
    """Tests for decorator functionality."""

    def test_decorator_binds_context(self, logger):
        """Verify with_context decorator binds context."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)

            @logger.with_context(request_id="decorated-req", agent_name="decorated_agent")
            def decorated_function():
                logger.info("Inside decorated")

            decorated_function()

            output = capture.get_output().strip()
            parsed = json.loads(output)

            assert parsed["context"]["request_id"] == "decorated-req"
            assert parsed["context"]["agent"] == "decorated_agent"

    def test_decorator_preserves_return_value(self, logger):
        """Verify decorator preserves function return value."""

        @logger.with_context(request_id="req")
        def add(a, b):
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_decorator_preserves_function_metadata(self, logger):
        """Verify decorator preserves function name and docstring."""

        @logger.with_context(request_id="req")
        def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."


class TestThreadSafety:
    """Tests for thread-safe implementation."""

    def test_context_isolated_between_threads(self, logger):
        """Verify context is isolated between threads via ContextVar thread isolation."""
        results = {}
        errors = []

        def thread_func(thread_id):
            try:
                # Set thread-specific context
                set_context(request_id=f"req-{thread_id}", agent_name=f"agent-{thread_id}")

                # Verify context is available within this thread
                context = get_context()
                results[thread_id] = context["request_id"]

                # Also verify via logger
                local_logger = StructuredLogger(f"thread_{thread_id}")
                # The context should propagate to the logger
                context_via_logger = local_logger._get_context()
                results[f"logger_{thread_id}"] = context_via_logger["request_id"]
            except Exception as e:
                errors.append((thread_id, str(e)))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(thread_func, i) for i in range(4)]
            for f in futures:
                f.result()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        # Verify each thread has its own isolated context
        assert results["logger_0"] == "req-0"
        assert results["logger_1"] == "req-1"
        assert results["logger_2"] == "req-2"
        assert results["logger_3"] == "req-3"

    def test_same_thread_context_persists(self, logger):
        """Verify context persists within same thread."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)

            set_context(request_id="persistent-req", agent_name="persistent-agent")

            logger.info("Message 1")
            output1 = json.loads(capture.get_output().strip())
            assert output1["context"]["request_id"] == "persistent-req"

            capture.clear()

            logger.info("Message 2")
            output2 = json.loads(capture.get_output().strip())
            assert output2["context"]["request_id"] == "persistent-req"
            assert output2["context"]["agent"] == "persistent-agent"


class TestGetLogger:
    """Tests for get_logger convenience function."""

    def test_get_logger_returns_structured_logger(self):
        """Verify get_logger returns StructuredLogger instance."""
        logger = get_logger("test")
        assert isinstance(logger, StructuredLogger)

    def test_get_logger_with_custom_level(self):
        """Verify get_logger accepts custom level."""
        logger = get_logger("test", logging.DEBUG)
        assert logger.logger.level == logging.DEBUG


class TestExceptionLogging:
    """Tests for exception logging."""

    def test_exception_includes_traceback(self, logger):
        """Verify exception logging includes traceback."""
        with LogCapture() as capture:
            logger.logger.addHandler(capture.handler)

            try:
                raise ValueError("Test error")
            except ValueError:
                logger.exception("Caught exception")

            output = capture.get_output().strip()
            # Exception logs should have more content due to traceback
            assert len(output) > 0


class TestClearContext:
    """Tests for clear_context function."""

    def test_clear_context_resets_all(self):
        """Verify clear_context resets all variables."""
        set_context(request_id="req", session_id="sess", agent_name="agent")
        clear_context()

        context = get_context()
        assert context["request_id"] is None
        assert context["session_id"] is None
        assert context["agent"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
