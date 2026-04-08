"""
Async retry policy with exponential backoff and jitter for handling transient failures.
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


class HTTPRetryableError(Exception):
    """Base class for HTTP errors that are retryable."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class ConnectionError(Exception):
    """Connection error indicating network issues."""
    pass


class TimeoutError(Exception):
    """Timeout error indicating request took too long."""
    pass


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: float = 0.1,
    retry_on: Tuple[Type[Exception], ...] = (Exception,),
    do_not_retry_on: Tuple[Type[Exception], ...] = (),
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504),
    non_retryable_status_codes: Tuple[int, ...] = (400, 401, 403),
):
    """
    Async retry decorator with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay in seconds (default: 30.0)
        jitter: Jitter factor (0.0-1.0) to prevent thundering herd (default: 0.1)
        retry_on: Tuple of exception types to retry on (default: all exceptions)
        do_not_retry_on: Tuple of exception types to NOT retry on
        retryable_status_codes: HTTP status codes that trigger retry (default: 429, 500-504)
        non_retryable_status_codes: HTTP status codes that never trigger retry (default: 400, 401, 403)

    Returns:
        Decorated function with retry logic

    Example:
        @async_retry(max_attempts=3, base_delay=1.0, jitter=0.2)
        async def fetch_data():
            return await client.get()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except do_not_retry_on as e:
                    # Do not retry these exceptions
                    logger.warning(
                        f"Function {func.__name__} failed with non-retryable exception "
                        f"{type(e).__name__}: {e}"
                    )
                    raise

                except HTTPRetryableError as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} exhausted all {max_attempts} attempts "
                            f"(HTTP {e.status_code})"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts due to HTTP {e.status_code}",
                            last_exception=e
                        ) from e

                    delay = _calculate_delay(attempt, base_delay, max_delay, jitter)
                    logger.warning(
                        f"Function {func.__name__} attempt {attempt}/{max_attempts} failed "
                        f"with HTTP {e.status_code}. Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} exhausted all {max_attempts} attempts "
                            f"({type(e).__name__}: {e})"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {type(e).__name__}",
                            last_exception=e
                        ) from e

                    delay = _calculate_delay(attempt, base_delay, max_delay, jitter)
                    logger.warning(
                        f"Function {func.__name__} attempt {attempt}/{max_attempts} failed "
                        f"({type(e).__name__}: {e}). Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

                except Exception as e:
                    # Catch-all for unexpected exceptions not in retry_on
                    if not retry_on or Exception not in retry_on:
                        logger.error(
                            f"Function {func.__name__} failed with unexpected exception "
                            f"{type(e).__name__}: {e}"
                        )
                        raise

                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} exhausted all {max_attempts} attempts "
                            f"(unexpected: {type(e).__name__}: {e})"
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts: {type(e).__name__}",
                            last_exception=e
                        ) from e

                    delay = _calculate_delay(attempt, base_delay, max_delay, jitter)
                    logger.warning(
                        f"Function {func.__name__} attempt {attempt}/{max_attempts} failed "
                        f"(unexpected: {type(e).__name__}: {e}). Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            # Should not reach here, but safety net
            if last_exception:
                raise RetryExhaustedError(
                    f"Failed after {max_attempts} attempts",
                    last_exception=last_exception
                )

        return wrapper

    return decorator


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter: float
) -> float:
    """
    Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (1-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Jitter factor (0.0-1.0)

    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * 2^(attempt-1)
    exponential_delay = base_delay * (2 ** (attempt - 1))

    # Cap at max_delay
    capped_delay = min(exponential_delay, max_delay)

    # Add jitter to prevent thundering herd
    if jitter > 0:
        jitter_range = capped_delay * jitter
        random_jitter = random.uniform(-jitter_range, jitter_range)
        final_delay = capped_delay + random_jitter
    else:
        final_delay = capped_delay

    # Ensure delay is non-negative
    return max(0.0, final_delay)


def is_retryable_http_status(status_code: int) -> bool:
    """
    Check if an HTTP status code is retryable.

    Args:
        status_code: HTTP status code

    Returns:
        True if the status code indicates a retryable error
    """
    retryable_codes = (408, 429, 500, 502, 503, 504)
    return status_code in retryable_codes


def is_non_retryable_http_status(status_code: int) -> bool:
    """
    Check if an HTTP status code is non-retryable.

    Args:
        status_code: HTTP status code

    Returns:
        True if the status code should NOT be retried
    """
    non_retryable_codes = (400, 401, 403, 404, 405, 410, 422)
    return status_code in non_retryable_codes
