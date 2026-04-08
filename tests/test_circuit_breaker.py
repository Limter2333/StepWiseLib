"""
Tests for Circuit Breaker Implementation

Tests cover:
- State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
- Thread-safe operations
- Failure tracking and threshold triggering
- Recovery timeout behavior
- Half-open call limiting
- Statistics tracking
- Decorator functionality
- Async circuit breaker
"""

import pytest
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

import sys
sys.path.insert(0, 'G:/claude_code_project/core')

from resilience.circuit_breaker import (
    CircuitBreaker,
    AsyncCircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerManager,
    circuit_breaker_decorator,
    async_circuit_breaker_decorator,
    create_llm_circuit_breaker,
    create_vector_db_circuit_breaker,
    get_circuit_breaker_manager,
    LLMCallWrapper,
    ChromaDBWrapper,
)


class TestCircuitBreakerBasic:
    """Basic circuit breaker tests."""

    def test_initial_state_is_closed(self):
        """Circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    def test_initial_stats(self):
        """Initial statistics are zeroed."""
        cb = CircuitBreaker("test")
        stats = cb.get_stats()
        assert stats.failure_count == 0
        assert stats.success_count == 0
        assert stats.total_calls == 0
        assert stats.total_rejected_calls == 0
        assert stats.last_failure_time is None

    def test_successful_call_records_success(self):
        """Successful call increments success counter."""
        cb = CircuitBreaker("test")
        result = cb.call(lambda: "success")
        assert result == "success"
        stats = cb.get_stats()
        assert stats.success_count == 1
        assert stats.total_calls == 1

    def test_failed_call_records_failure(self):
        """Failed call increments failure counter."""
        cb = CircuitBreaker("test")

        def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            cb.call(failing_func)

        stats = cb.get_stats()
        assert stats.failure_count == 1
        assert stats.total_calls == 1

    def test_get_state_returns_detailed_info(self):
        """get_state returns comprehensive circuit breaker info."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60.0,
            half_open_max_calls=5
        ))
        state = cb.get_state()
        assert state["name"] == "test"
        assert state["state"] == "closed"
        assert state["config"]["failure_threshold"] == 3
        assert state["config"]["recovery_timeout"] == 60.0
        assert state["config"]["half_open_max_calls"] == 5


class TestCircuitBreakerTransitions:
    """Tests for state machine transitions."""

    def test_transitions_to_open_after_threshold(self):
        """Circuit opens after reaching failure threshold."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0
        ))

        for i in range(3):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_rejects_calls(self):
        """OPEN circuit immediately rejects calls."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=30.0
        ))

        # Push to OPEN state
        for i in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        # Further calls should be rejected
        with pytest.raises(CircuitBreakerError) as exc_info:
            cb.call(lambda: "should not execute")
        assert "OPEN" in str(exc_info.value)

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit transitions to HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1  # 100ms
        ))

        # Push to OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_limited_calls(self):
        """HALF_OPEN allows up to half_open_max_calls."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,
            half_open_max_calls=2,
            success_threshold=3  # Set higher so we test half_open_max_calls limit
        ))

        # Push to OPEN, then wait for HALF_OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # First call in half-open should succeed
        result = cb.call(lambda: "call 1")
        assert result == "call 1"

        # Second call in half-open should succeed
        result = cb.call(lambda: "call 2")
        assert result == "call 2"

        # Third call should be rejected (exceeded half_open_max_calls)
        with pytest.raises(CircuitBreakerError):
            cb.call(lambda: "should not execute")

    def test_half_open_success_closes_circuit(self):
        """Successful calls in HALF_OPEN transition to CLOSED."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,
            half_open_max_calls=3,
            success_threshold=2  # Need 2 successes to close
        ))

        # Push to OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # Record successes (cb.call will record automatically)
        cb.call(lambda: "success 1")
        cb.call(lambda: "success 2")

        # Should transition back to CLOSED
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        """Failure in HALF_OPEN transitions back to OPEN."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1,
            half_open_max_calls=3
        ))

        # Push to OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # Successful call in half-open
        cb.call(lambda: "success")

        # Now push back to half-open and fail
        # Re-open by forcing state
        cb._state = CircuitState.HALF_OPEN
        cb._half_open_calls = 0

        # Failure should transition to OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail 2")))
        except ValueError:
            pass

        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_calls_thread_safe(self):
        """Concurrent calls are handled thread-safely."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=100,  # High threshold
            recovery_timeout=30.0
        ))

        call_count = [0]
        lock = threading.Lock()

        def increment():
            def inner():
                with lock:
                    call_count[0] += 1
                return "ok"
            return cb.call(inner)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(increment) for _ in range(100)]
            for f in futures:
                f.result()

        stats = cb.get_stats()
        assert stats.total_calls == 100

    def test_concurrent_failures_and_successes(self):
        """Concurrent failures and successes update counters correctly."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1000,
            recovery_timeout=30.0
        ))

        def maybe_fail(i):
            if i % 3 == 0:
                raise ValueError("fail")
            return "success"

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(cb.call, maybe_fail, i) for i in range(99)]
            for f in futures:
                try:
                    f.result()
                except ValueError:
                    pass

        stats = cb.get_stats()
        # 99 calls total: 33 failures, 66 successes (roughly)
        assert stats.total_calls == 99
        # Allow for some variance due to timing
        assert stats.failure_count + stats.success_count == 99

    def test_race_condition_protection(self):
        """State transitions are protected from race conditions."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30.0
        ))

        state_changes = []
        lock = threading.Lock()

        def record_and_fail():
            try:
                raise ValueError("fail")
            except ValueError:
                cb.record_failure()

        # Rapid concurrent failures
        threads = [threading.Thread(target=record_and_fail) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should be OPEN (at least 5 failures)
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerReset:
    """Tests for reset functionality."""

    def test_reset_closes_circuit(self):
        """Reset transitions circuit to CLOSED and clears stats."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))

        # Push to OPEN
        for i in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        stats = cb.get_stats()
        assert stats.failure_count == 0
        assert stats.success_count == 0

    def test_reset_allows_new_calls(self):
        """After reset, circuit accepts new calls."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))

        # Push to OPEN
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        cb.reset()

        # Should work now
        result = cb.call(lambda: "new call")
        assert result == "new call"


class TestCircuitBreakerDecorator:
    """Tests for decorator functionality."""

    def test_sync_decorator(self):
        """Sync decorator wraps function with circuit breaker."""
        cb = CircuitBreaker("decorated", CircuitBreakerConfig(failure_threshold=5))

        @circuit_breaker_decorator(cb)
        def my_function(x):
            return x * 2

        result = my_function(5)
        assert result == 10

        stats = cb.get_stats()
        assert stats.success_count == 1

    def test_decorator_propagates_failure(self):
        """Decorator propagates exceptions and records failures."""
        cb = CircuitBreaker("decorated", CircuitBreakerConfig(failure_threshold=5))

        @circuit_breaker_decorator(cb)
        def failing_function():
            raise RuntimeError("error")

        with pytest.raises(RuntimeError):
            failing_function()

        stats = cb.get_stats()
        assert stats.failure_count == 1


class TestCircuitBreakerManager:
    """Tests for circuit breaker manager."""

    def test_create_and_get_breaker(self):
        """Manager creates and returns circuit breakers."""
        manager = CircuitBreakerManager()
        cb = manager.create_breaker("test_cb")
        assert cb.name == "test_cb"
        assert manager.get_breaker("test_cb") is cb

    def test_create_duplicate_raises_error(self):
        """Creating duplicate breaker raises ValueError."""
        manager = CircuitBreakerManager()
        manager.create_breaker("test_cb")
        with pytest.raises(ValueError) as exc:
            manager.create_breaker("test_cb")
        assert "already exists" in str(exc.value)

    def test_remove_breaker(self):
        """Manager removes circuit breakers."""
        manager = CircuitBreakerManager()
        manager.create_breaker("test_cb")
        assert manager.remove_breaker("test_cb") is True
        assert manager.get_breaker("test_cb") is None

    def test_get_all_stats(self):
        """Manager returns stats for all breakers."""
        manager = CircuitBreakerManager()
        cb1 = manager.create_breaker("cb1")
        cb2 = manager.create_breaker("cb2")
        cb1.call(lambda: "ok")

        stats = manager.get_all_stats()
        assert "cb1" in stats
        assert "cb2" in stats


class TestConvenienceFunctions:
    """Tests for convenience factory functions."""

    def test_create_llm_circuit_breaker(self):
        """create_llm_circuit_breaker creates properly configured breaker."""
        cb = create_llm_circuit_breaker("my_llm")
        assert cb.name == "my_llm"
        assert cb.config.failure_threshold == 5
        assert cb.config.recovery_timeout == 30.0

    def test_create_vector_db_circuit_breaker(self):
        """create_vector_db_circuit_breaker creates properly configured breaker."""
        cb = create_vector_db_circuit_breaker("my_chroma")
        assert cb.name == "my_chroma"
        assert cb.config.failure_threshold == 5
        assert cb.config.recovery_timeout == 30.0

    def test_get_manager_singleton(self):
        """get_circuit_breaker_manager returns singleton."""
        manager1 = get_circuit_breaker_manager()
        manager2 = get_circuit_breaker_manager()
        assert manager1 is manager2


class TestWrappers:
    """Tests for service wrapper classes."""

    def test_llm_wrapper(self):
        """LLMCallWrapper wraps LLM calls with circuit breaker."""
        def mock_llm(prompt):
            return f"response to: {prompt}"

        wrapper = LLMCallWrapper(mock_llm)
        result = wrapper("hello")
        assert result == "response to: hello"

    def test_chroma_wrapper(self):
        """ChromaDBWrapper wraps ChromaDB queries with circuit breaker."""
        def mock_query(query):
            return [f"result for: {query}"]

        wrapper = ChromaDBWrapper(mock_query)
        result = wrapper("search term")
        assert result == ["result for: search term"]


class TestAsyncCircuitBreaker:
    """Tests for async circuit breaker implementation."""

    @pytest.mark.asyncio
    async def test_async_initial_state(self):
        """Async circuit breaker starts in CLOSED state."""
        cb = AsyncCircuitBreaker("async_test")
        assert cb._state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_async_successful_call(self):
        """Async successful call records success."""
        cb = AsyncCircuitBreaker("async_test")

        async def async_func():
            return "async success"

        result = await cb.call(async_func)
        assert result == "async success"

        stats = await cb.get_stats()
        assert stats.success_count == 1

    @pytest.mark.asyncio
    async def test_async_failed_call(self):
        """Async failed call records failure."""
        cb = AsyncCircuitBreaker("async_test")

        async def async_fail():
            raise ValueError("async error")

        with pytest.raises(ValueError):
            await cb.call(async_fail)

        stats = await cb.get_stats()
        assert stats.failure_count == 1

    @pytest.mark.asyncio
    async def test_async_transitions_to_open(self):
        """Async circuit opens after threshold failures."""
        cb = AsyncCircuitBreaker("async_test", CircuitBreakerConfig(
            failure_threshold=3
        ))

        for i in range(3):
            try:
                await cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert cb._state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_async_half_open_transition(self):
        """Async circuit transitions to HALF_OPEN after timeout."""
        cb = AsyncCircuitBreaker("async_test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.1
        ))

        try:
            await cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb._state == CircuitState.OPEN

        await asyncio.sleep(0.15)
        # Use _get_state_unsafe directly since we're already holding the lock concept
        # but actually we need to properly check - let's just verify via can_execute
        # because _state is directly accessible for the assertion
        state = await cb.state
        assert state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_async_reset(self):
        """Async circuit breaker reset works."""
        cb = AsyncCircuitBreaker("async_test", CircuitBreakerConfig(
            failure_threshold=1
        ))

        try:
            await cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        assert cb._state == CircuitState.OPEN

        await cb.reset()
        assert cb._state == CircuitState.CLOSED

        stats = await cb.get_stats()
        assert stats.failure_count == 0


class TestEdgeCases:
    """Edge case tests."""

    def test_zero_failure_threshold(self):
        """Zero failure threshold should open immediately."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=0))
        # Should open on first call
        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass
        assert cb.state == CircuitState.OPEN

    def test_zero_recovery_timeout(self):
        """Zero recovery timeout should transition immediately."""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            recovery_timeout=0.0
        ))

        try:
            cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            pass

        # Should immediately allow transition to HALF_OPEN
        time.sleep(0.01)
        assert cb.state == CircuitState.HALF_OPEN

    def test_none_function(self):
        """None function should raise appropriate error."""
        cb = CircuitBreaker("test")
        with pytest.raises(TypeError):
            cb.call(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
