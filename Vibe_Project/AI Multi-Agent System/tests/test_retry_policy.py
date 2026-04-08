"""
Tests for the async retry policy with exponential backoff.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, call
import logging

from core.resilience.retry_policy import (
    async_retry,
    RetryExhaustedError,
    _calculate_delay,
    is_retryable_http_status,
    is_non_retryable_http_status,
)


class TestCalculateDelay:
    """Tests for delay calculation with exponential backoff and jitter."""

    def test_exponential_backoff_no_jitter(self):
        """Test exponential backoff without jitter."""
        delay = _calculate_delay(attempt=1, base_delay=1.0, max_delay=30.0, jitter=0.0)
        assert delay == 1.0

        delay = _calculate_delay(attempt=2, base_delay=1.0, max_delay=30.0, jitter=0.0)
        assert delay == 2.0

        delay = _calculate_delay(attempt=3, base_delay=1.0, max_delay=30.0, jitter=0.0)
        assert delay == 4.0

    def test_exponential_backoff_with_max_delay(self):
        """Test that delay is capped at max_delay."""
        delay = _calculate_delay(attempt=10, base_delay=1.0, max_delay=10.0, jitter=0.0)
        assert delay == 10.0

        delay = _calculate_delay(attempt=5, base_delay=10.0, max_delay=30.0, jitter=0.0)
        assert delay == 30.0

    def test_exponential_backoff_with_jitter(self):
        """Test that jitter adds randomness to delay."""
        base_delay = 1.0
        max_delay = 30.0
        jitter = 0.1

        delays = [_calculate_delay(1, base_delay, max_delay, jitter) for _ in range(100)]

        # All delays should be around base_delay +/- jitter
        for delay in delays:
            assert 0.9 <= delay <= 1.1, f"Delay {delay} outside expected range"

        # Should have some variation
        unique_delays = set(delays)
        assert len(unique_delays) > 1, "Jitter should produce varied delays"

    def test_zero_jitter(self):
        """Test that zero jitter produces consistent delays."""
        delay1 = _calculate_delay(attempt=1, base_delay=2.0, max_delay=30.0, jitter=0.0)
        delay2 = _calculate_delay(attempt=1, base_delay=2.0, max_delay=30.0, jitter=0.0)
        assert delay1 == delay2 == 2.0

    def test_negative_delay_prevented(self):
        """Test that delay is never negative even with jitter."""
        # Even with extreme jitter values, delay should not go negative
        delay = _calculate_delay(attempt=1, base_delay=0.1, max_delay=0.5, jitter=1.0)
        assert delay >= 0.0


class TestHTTPStatusChecks:
    """Tests for HTTP status code retryability checks."""

    @pytest.mark.parametrize("status_code", [429, 500, 502, 503, 504])
    def test_retryable_status_codes(self, status_code):
        """Test that rate limit and server error codes are retryable."""
        assert is_retryable_http_status(status_code) is True
        assert is_non_retryable_http_status(status_code) is False

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404, 405])
    def test_non_retryable_status_codes(self, status_code):
        """Test that client error codes are not retryable."""
        assert is_non_retryable_http_status(status_code) is True


class TestAsyncRetryDecorator:
    """Tests for the async_retry decorator."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Test that successful calls are not retried."""
        call_count = 0

        @async_retry(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_exception(self):
        """Test that exceptions trigger retries."""
        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausted_retries_raises_error(self):
        """Test that exhausted retries raise RetryExhaustedError."""
        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_fails()

        assert call_count == 3
        assert "Failed after 3 attempts" in str(exc_info.value)
        assert exc_info.value.last_exception is not None

    @pytest.mark.asyncio
    async def test_no_retry_on_excluded_exception(self):
        """Test that excluded exceptions are not retried."""
        call_count = 0

        @async_retry(
            max_attempts=3,
            base_delay=0.01,
            do_not_retry_on=(ValueError,)
        )
        async def non_retryable_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            await non_retryable_func()

        assert call_count == 1  # Only called once, no retries

    @pytest.mark.asyncio
    async def test_custom_retry_on_types(self):
        """Test custom retry_on exception types."""
        call_count = 0

        @async_retry(
            max_attempts=3,
            base_delay=0.01,
            retry_on=(ConnectionError, TimeoutError)
        )
        async def custom_retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Custom retry")
            return "success"

        result = await custom_retry_func()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_with_delay(self):
        """Test that retries occur with proper delays."""
        call_times = []

        original_time = 0

        @async_retry(max_attempts=3, base_delay=0.1, jitter=0.0)
        async def timed_flaky_func():
            call_times.append(asyncio.get_event_loop().time() - original_time)
            if len(call_times) < 3:
                raise ConnectionError("Flaky")
            return "success"

        original_time = asyncio.get_event_loop().time()
        await timed_flaky_func()

        # Check that delays increase exponentially
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]  # ~0.1s
        delay2 = call_times[2] - call_times[1]  # ~0.2s

        assert 0.08 <= delay1 <= 0.15
        assert 0.15 <= delay2 <= 0.30

    @pytest.mark.asyncio
    async def test_retry_does_not_modify_args(self):
        """Test that retry decorator preserves function arguments."""
        received_args = []
        received_kwargs = {}

        @async_retry(max_attempts=3, base_delay=0.01)
        async def func_with_args(arg1, arg2, kwarg1=None, kwarg2=None):
            received_args.append(arg1)
            received_kwargs["kwarg1"] = kwarg1
            received_kwargs["kwarg2"] = kwarg2
            if len(received_args) < 2:
                raise ConnectionError("Retry")
            return f"{arg1}-{arg2}-{kwarg1}-{kwarg2}"

        result = await func_with_args("a", "b", kwarg1="c", kwarg2="d")
        assert result == "a-b-c-d"
        assert received_args == ["a", "a"]
        assert received_kwargs["kwarg1"] == "c"
        assert received_kwargs["kwarg2"] == "d"

    @pytest.mark.asyncio
    async def test_async_retry_preserves_return_value(self):
        """Test that async functions returning complex objects work correctly."""
        expected_data = {"key": "value", "nested": {"data": [1, 2, 3]}}

        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.01)
        async def complex_return_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Retry")
            return expected_data

        result = await complex_return_func()
        assert result == expected_data
        assert call_count == 2


class TestRetryLogging:
    """Tests for retry logging behavior."""

    @pytest.mark.asyncio
    async def test_logs_warning_on_retry(self, caplog):
        """Test that warnings are logged on retry attempts."""
        caplog.set_level(logging.WARNING)

        call_count = 0

        @async_retry(max_attempts=3, base_delay=0.01)
        async def flaky_with_logging():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Flaky connection")
            return "success"

        await flaky_with_logging()

        # Check that warnings were logged
        warning_messages = [record.message for record in caplog.records if record.levelno == logging.WARNING]
        assert len(warning_messages) == 2  # 2 retries before success

        for msg in warning_messages:
            assert "attempt" in msg.lower() or "retry" in msg.lower()

    @pytest.mark.asyncio
    async def test_logs_error_on_exhaustion(self, caplog):
        """Test that errors are logged when retries are exhausted."""
        caplog.set_level(logging.ERROR)

        @async_retry(max_attempts=3, base_delay=0.01)
        async def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RetryExhaustedError):
            await always_fails()

        error_messages = [record.message for record in caplog.records if record.levelno == logging.ERROR]
        assert len(error_messages) >= 1
        assert any("exhausted" in msg.lower() for msg in error_messages)


class TestRetryExhaustedError:
    """Tests for RetryExhaustedError exception."""

    def test_error_message_format(self):
        """Test that error message is properly formatted."""
        original_error = ConnectionError("Connection refused")
        error = RetryExhaustedError("Failed after 3 attempts", last_exception=original_error)

        assert "Failed after 3 attempts" in str(error)
        assert error.last_exception is original_error

    def test_error_chaining(self):
        """Test that exception stores last_exception properly."""
        original_error = ConnectionError("Original error")
        error = RetryExhaustedError("Final error", last_exception=original_error)

        # Check that the original exception is stored in last_exception
        assert error.last_exception is original_error


class TestDecoratorParameters:
    """Tests for various decorator parameter combinations."""

    @pytest.mark.asyncio
    async def test_max_attempts_one(self):
        """Test behavior with max_attempts=1 (no retries)."""
        call_count = 0

        @async_retry(max_attempts=1, base_delay=0.01)
        async def single_attempt_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Single attempt")

        with pytest.raises(RetryExhaustedError):
            await single_attempt_func()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_large_base_delay_capped(self):
        """Test that large base delays don't cause issues."""
        call_count = 0

        @async_retry(max_attempts=3, base_delay=100.0, max_delay=0.2, jitter=0.0)
        async def capped_delay_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Flaky")
            return "success"

        result = await capped_delay_func()
        assert result == "success"
        # Delay should be capped at max_delay
        assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
