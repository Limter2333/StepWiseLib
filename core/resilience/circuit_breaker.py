"""
Circuit Breaker Pattern Implementation for AI Multi-Agent System

Prevents cascading failures when external services (LLM, vector DB) fail.
Implements state machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED/Open
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Optional, Any, TypeVar, Generic
import threading
import time
import asyncio
from functools import wraps

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing fast, requests are rejected
    HALF_OPEN = "half_open"  # Testing recovery, limited requests pass through


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open and rejects requests."""
    def __init__(self, message: str = "Circuit breaker is OPEN", circuit_state: CircuitState = CircuitState.OPEN):
        self.message = message
        self.circuit_state = circuit_state
        super().__init__(self.message)


class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Raised when recovery timeout expires in half-open state."""
    def __init__(self, message: str = "Circuit breaker recovery timeout expired"):
        super().__init__(message, CircuitState.HALF_OPEN)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5          # Number of failures before opening circuit
    recovery_timeout: float = 30.0     # Seconds before attempting recovery
    half_open_max_calls: int = 3       # Max calls allowed in half-open state
    success_threshold: int = 2          # Successes needed in half-open to close (optional enhancement)


@dataclass
class CircuitBreakerStats:
    """Statistics tracked by circuit breaker."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    total_calls: int = 0
    total_rejected_calls: int = 0
    state_changes: int = 0


class CircuitBreaker:
    """
    Thread-safe circuit breaker implementation.

    State Machine:
    - CLOSED: Normal operation. Requests pass through. Failures increment counter.
              When failures >= threshold, transition to OPEN.
    - OPEN: Failing fast. Requests are rejected immediately.
            After recovery_timeout, transition to HALF_OPEN.
    - HALF_OPEN: Testing recovery. Limited requests pass through.
                 If successes >= success_threshold, transition to CLOSED.
                 If failures occur, transition back to OPEN.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = threading.RLock()
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get current circuit state (thread-safe)."""
        with self._lock:
            return self._get_state_unsafe()

    def _get_state_unsafe(self) -> CircuitState:
        """Get state without lock acquisition - caller must hold lock."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has expired
            if self._stats.last_failure_time is not None:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state (thread-safe). Caller must hold lock."""
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            self._stats.state_changes += 1
            if new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
            elif new_state == CircuitState.CLOSED:
                self._stats.failure_count = 0
                self._half_open_calls = 0

    def record_success(self) -> None:
        """Record a successful call (thread-safe)."""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.success_count += 1

            if self._state == CircuitState.HALF_OPEN:
                # Increment half-open call counter
                self._half_open_calls += 1
                # Check if we've reached success threshold to close circuit
                success_threshold = getattr(self.config, 'success_threshold', 2)
                if self._stats.success_count >= success_threshold:
                    self._transition_to(CircuitState.CLOSED)

    def record_failure(self, exc: Optional[Exception] = None) -> None:
        """Record a failed call (thread-safe)."""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.failure_count += 1
            self._stats.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open opens the circuit
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def can_execute(self) -> bool:
        """Check if a request can be executed (thread-safe)."""
        with self._lock:
            current_state = self._get_state_unsafe()
            if current_state == CircuitState.CLOSED:
                # In CLOSED state, allow calls but track successes
                return True
            elif current_state == CircuitState.OPEN:
                self._stats.total_rejected_calls += 1
                return False
            elif current_state == CircuitState.HALF_OPEN:
                # In HALF_OPEN, check if we've met success threshold (transition to CLOSED)
                # or if we've exceeded half_open_max_calls
                success_threshold = getattr(self.config, 'success_threshold', 2)
                if self._half_open_calls < self.config.half_open_max_calls:
                    # Allow the call; record_success will handle incrementing and transition
                    return True
                else:
                    self._stats.total_rejected_calls += 1
                    return False
            return False

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function through the circuit breaker (synchronous).

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of function execution

        Raises:
            CircuitBreakerError: If circuit is open and rejecting requests
        """
        if not self.can_execute():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN - request rejected",
                self.state
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise

    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics (thread-safe)."""
        with self._lock:
            return CircuitBreakerStats(
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                last_failure_time=self._stats.last_failure_time,
                total_calls=self._stats.total_calls,
                total_rejected_calls=self._stats.total_rejected_calls,
                state_changes=self._stats.state_changes
            )

    def get_state(self) -> dict:
        """Get detailed state information (thread-safe)."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._get_state_unsafe().value,
                "failure_count": self._stats.failure_count,
                "success_count": self._stats.success_count,
                "last_failure_time": self._stats.last_failure_time,
                "total_calls": self._stats.total_calls,
                "total_rejected_calls": self._stats.total_rejected_calls,
                "state_changes": self._stats.state_changes,
                "half_open_calls": self._half_open_calls,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "half_open_max_calls": self.config.half_open_max_calls,
                }
            }

    def reset(self) -> None:
        """Reset circuit breaker to initial CLOSED state (thread-safe)."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitBreakerStats()
            self._half_open_calls = 0


class AsyncCircuitBreaker:
    """
    Async-aware thread-safe circuit breaker implementation.

    Same state machine as CircuitBreaker but supports async/await operations.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        self._half_open_calls = 0

    @property
    async def state(self) -> CircuitState:
        """Get current circuit state (async, thread-safe)."""
        async with self._lock:
            return await self._get_state_unsafe()

    async def _get_state_unsafe(self) -> CircuitState:
        """Get state without lock acquisition - caller must hold lock."""
        if self._state == CircuitState.OPEN:
            if self._stats.last_failure_time is not None:
                elapsed = time.time() - self._stats.last_failure_time
                if elapsed >= self.config.recovery_timeout:
                    await self._transition_to(CircuitState.HALF_OPEN)
        return self._state

    async def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state (async, thread-safe). Caller must hold lock."""
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            self._stats.state_changes += 1
            if new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
            elif new_state == CircuitState.CLOSED:
                self._stats.failure_count = 0
                self._half_open_calls = 0

    async def record_success(self) -> None:
        """Record a successful call (async, thread-safe)."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.success_count += 1

            if self._state == CircuitState.HALF_OPEN:
                # Increment half-open call counter
                self._half_open_calls += 1
                # Check if we've reached success threshold to close circuit
                success_threshold = getattr(self.config, 'success_threshold', 2)
                if self._stats.success_count >= success_threshold:
                    await self._transition_to(CircuitState.CLOSED)

    async def record_failure(self, exc: Optional[Exception] = None) -> None:
        """Record a failed call (async, thread-safe)."""
        async with self._lock:
            self._stats.total_calls += 1
            self._stats.failure_count += 1
            self._stats.last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                await self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._stats.failure_count >= self.config.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

    async def can_execute(self) -> bool:
        """Check if a request can be executed (async, thread-safe)."""
        async with self._lock:
            current_state = await self._get_state_unsafe()
            if current_state == CircuitState.CLOSED:
                # In CLOSED state, allow calls but track successes
                return True
            elif current_state == CircuitState.OPEN:
                self._stats.total_rejected_calls += 1
                return False
            elif current_state == CircuitState.HALF_OPEN:
                # In HALF_OPEN, check if we've met success threshold (transition to CLOSED)
                # or if we've exceeded half_open_max_calls
                success_threshold = getattr(self.config, 'success_threshold', 2)
                if self._half_open_calls < self.config.half_open_max_calls:
                    # Allow the call; record_success will handle incrementing and transition
                    return True
                else:
                    self._stats.total_rejected_calls += 1
                    return False
            return False

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute an async function through the circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Result of async function execution

        Raises:
            CircuitBreakerError: If circuit is open and rejecting requests
        """
        if not await self.can_execute():
            state = await self.state
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN - request rejected",
                state
            )

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure(e)
            raise

    async def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics (async, thread-safe)."""
        async with self._lock:
            return CircuitBreakerStats(
                failure_count=self._stats.failure_count,
                success_count=self._stats.success_count,
                last_failure_time=self._stats.last_failure_time,
                total_calls=self._stats.total_calls,
                total_rejected_calls=self._stats.total_rejected_calls,
                state_changes=self._stats.state_changes
            )

    async def get_state(self) -> dict:
        """Get detailed state information (async, thread-safe)."""
        async with self._lock:
            return {
                "name": self.name,
                "state": (await self._get_state_unsafe()).value,
                "failure_count": self._stats.failure_count,
                "success_count": self._stats.success_count,
                "last_failure_time": self._stats.last_failure_time,
                "total_calls": self._stats.total_calls,
                "total_rejected_calls": self._stats.total_rejected_calls,
                "state_changes": self._stats.state_changes,
                "half_open_calls": self._half_open_calls,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "half_open_max_calls": self.config.half_open_max_calls,
                }
            }

    async def reset(self) -> None:
        """Reset circuit breaker to initial CLOSED state (async, thread-safe)."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._stats = CircuitBreakerStats()
            self._half_open_calls = 0


def circuit_breaker_decorator(breaker: CircuitBreaker):
    """
    Decorator to wrap a synchronous function with a circuit breaker.

    Usage:
        cb = CircuitBreaker("my_service")
        @circuit_breaker_decorator(cb)
        def my_function():
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


def async_circuit_breaker_decorator(breaker: AsyncCircuitBreaker):
    """
    Decorator to wrap an async function with a circuit breaker.

    Usage:
        cb = AsyncCircuitBreaker("my_service")
        @async_circuit_breaker_decorator(cb)
        async def my_async_function():
            pass
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


class CircuitBreakerManager:
    """
    Centralized manager for multiple circuit breakers.

    Provides a registry of circuit breakers for different services
    (LLM, ChromaDB, etc.) with convenient access.
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._async_breakers: dict[str, AsyncCircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get a synchronous circuit breaker by name."""
        with self._lock:
            return self._breakers.get(name)

    def get_async_breaker(self, name: str) -> Optional[AsyncCircuitBreaker]:
        """Get an async circuit breaker by name."""
        with self._lock:
            return self._async_breakers.get(name)

    def create_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        async_only: bool = False
    ) -> CircuitBreaker | AsyncCircuitBreaker:
        """
        Create and register a new circuit breaker.

        Args:
            name: Unique name for the circuit breaker
            config: Optional configuration
            async_only: If True, only creates async breaker

        Returns:
            Created circuit breaker instance
        """
        with self._lock:
            if name in self._breakers or name in self._async_breakers:
                raise ValueError(f"Circuit breaker '{name}' already exists")

            if async_only:
                breaker = AsyncCircuitBreaker(name, config)
                self._async_breakers[name] = breaker
                return breaker
            else:
                breaker = CircuitBreaker(name, config)
                self._breakers[name] = breaker
                return breaker

    def remove_breaker(self, name: str) -> bool:
        """Remove a circuit breaker by name. Returns True if removed."""
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                return True
            if name in self._async_breakers:
                del self._async_breakers[name]
                return True
            return False

    def get_all_stats(self) -> dict[str, dict]:
        """Get statistics for all registered circuit breakers."""
        with self._lock:
            stats = {}
            for name, breaker in self._breakers.items():
                stats[name] = breaker.get_state()
            for name, breaker in self._async_breakers.items():
                # For async, we need to get state synchronously if possible
                # or provide a method that doesn't require async context
                stats[name] = {
                    "name": name,
                    "state": breaker._state.value,
                    "type": "async"
                }
            return stats

    def reset_all(self) -> None:
        """Reset all circuit breakers to CLOSED state."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            # Note: AsyncCircuitBreaker.reset() is async, would need event loop


# Global circuit breaker manager instance
_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the global circuit breaker manager instance."""
    global _manager
    if _manager is None:
        _manager = CircuitBreakerManager()
    return _manager


def create_llm_circuit_breaker(
    name: str = "llm",
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0
) -> CircuitBreaker:
    """Create a circuit breaker for LLM service calls."""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=3
    )
    manager = get_circuit_breaker_manager()
    return manager.create_breaker(name, config)


def create_vector_db_circuit_breaker(
    name: str = "vector_db",
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0
) -> CircuitBreaker:
    """Create a circuit breaker for vector database (ChromaDB) calls."""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=3
    )
    manager = get_circuit_breaker_manager()
    return manager.create_breaker(name, config)


# Example usage wrappers for common external services
class LLMCallWrapper:
    """Wrapper for LLM calls with circuit breaker protection."""

    def __init__(
        self,
        llm_call: Callable[..., Any],
        breaker: Optional[CircuitBreaker] = None
    ):
        self.llm_call = llm_call
        self.breaker = breaker or create_llm_circuit_breaker()

    def __call__(self, *args, **kwargs):
        """Execute LLM call through circuit breaker."""
        return self.breaker.call(self.llm_call, *args, **kwargs)


class ChromaDBWrapper:
    """Wrapper for ChromaDB queries with circuit breaker protection."""

    def __init__(
        self,
        query_func: Callable[..., Any],
        breaker: Optional[CircuitBreaker] = None
    ):
        self.query_func = query_func
        self.breaker = breaker or create_vector_db_circuit_breaker()

    def __call__(self, *args, **kwargs):
        """Execute ChromaDB query through circuit breaker."""
        return self.breaker.call(self.query_func, *args, **kwargs)
