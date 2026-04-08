"""
Structured Logger for AI Multi-Agent System

Provides JSON-formatted logging with request context propagation,
thread-safe implementation using contextvars, and decorator/context manager support.
"""

import logging
import json
from datetime import datetime
from contextvars import ContextVar
from typing import Any, Dict, Optional
from functools import wraps
from enum import Enum
from copy import deepcopy

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
agent_name_var: ContextVar[Optional[str]] = ContextVar('agent_name', default=None)


class LogLevel(Enum):
    """Log level enumeration matching Python logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredLogger:
    """
    Structured logger with JSON output and context propagation.

    Features:
    - JSON output format for machine-readable logs
    - Automatic context binding (request_id, session_id, agent_name)
    - Thread-safe implementation using ContextVars
    - Context manager for temporary context overrides
    - Decorator for automatic context binding on functions

    Example:
        logger = StructuredLogger("my_agent")
        logger.info("Processing request", extra_field="value")

        # With decorator
        @logger.with_context(request_id="req-123", agent_name="my_agent")
        def process():
            logger.info("Inside decorated function")
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize the structured logger.

        Args:
            name: Logger name (typically module or agent name)
            level: Minimum log level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._name = name

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def setLevel(self, level: int):
        """Set the logging level for this logger."""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def _get_context(self) -> Dict[str, Any]:
        """Get current context as a dictionary."""
        return {
            "request_id": request_id_var.get(),
            "session_id": session_id_var.get(),
            "agent": agent_name_var.get(),
        }

    def _format_message(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """
        Format message as JSON with context.

        Args:
            msg: The log message
            extra: Additional fields to include in context

        Returns:
            JSON string with message, context, and timestamp
        """
        context = self._get_context()
        if extra:
            context.update(extra)

        log_entry = {
            "message": msg,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "logger": self._name
        }
        return json.dumps(log_entry, default=str)

    def _log(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None):
        """
        Internal log method that formats and delegates to Python logger.

        Args:
            level: Logging level (e.g., logging.INFO)
            msg: The log message
            extra: Additional context fields
        """
        formatted_msg = self._format_message(msg, extra)
        self.logger.log(level, formatted_msg)

    def debug(self, msg: str, **kwargs):
        """Log a debug message."""
        self._log(logging.DEBUG, msg, kwargs if kwargs else None)

    def info(self, msg: str, **kwargs):
        """Log an info message."""
        self._log(logging.INFO, msg, kwargs if kwargs else None)

    def warning(self, msg: str, **kwargs):
        """Log a warning message."""
        self._log(logging.WARNING, msg, kwargs if kwargs else None)

    def error(self, msg: str, **kwargs):
        """Log an error message."""
        self._log(logging.ERROR, msg, kwargs if kwargs else None)

    def critical(self, msg: str, **kwargs):
        """Log a critical message."""
        self._log(logging.CRITICAL, msg, kwargs if kwargs else None)

    def exception(self, msg: str, **kwargs):
        """Log an exception with traceback."""
        self._log(logging.ERROR, msg, kwargs if kwargs else None)
        self.logger.exception(msg)

    def bind(self, **kwargs):
        """
        Return a context manager for binding values to context variables.

        Example:
            with logger.bind(request_id="req-123"):
                logger.info("This will have request_id context")
        """
        return _LogContextManager(self._name, kwargs)

    def with_context(self, **kwargs):
        """
        Decorator to bind context for a function execution.

        Example:
            @logger.with_context(request_id="req-123", agent_name="my_agent")
            def my_function():
                logger.info("Context is available here")
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **func_kwargs):
                with self.bind(**kwargs):
                    return func(*args, **func_kwargs)
            return wrapper
        return decorator


class _LogContextManager:
    """
    Internal context manager for temporary context variable binding.

    Supports nested context managers and proper cleanup on exit.
    """

    def __init__(self, logger_name: str, context: Dict[str, Any]):
        self.logger_name = logger_name
        self.context = context
        self._tokens = {}

    def __enter__(self):
        """Bind context variables and store reset tokens."""
        for key, value in self.context.items():
            var = self._get_context_var(key)
            if var is not None:
                self._tokens[key] = var.set(value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset context variables to their previous values."""
        for key, token in self._tokens.items():
            var = self._get_context_var(key)
            if var is not None:
                var.reset(token)
        return False

    def _get_context_var(self, key: str) -> Optional[ContextVar]:
        """Get the context variable for a given key."""
        var_map = {
            'request_id': request_id_var,
            'session_id': session_id_var,
            'agent_name': agent_name_var,
            'agent': agent_name_var,
        }
        return var_map.get(key)


def set_context(**kwargs):
    """
    Set context variables globally.

    Args:
        request_id: Request identifier
        session_id: Session identifier
        agent_name: Agent name
    """
    if 'request_id' in kwargs:
        request_id_var.set(kwargs['request_id'])
    if 'session_id' in kwargs:
        session_id_var.set(kwargs['session_id'])
    if 'agent_name' in kwargs:
        agent_name_var.set(kwargs['agent_name'])
    if 'agent' in kwargs:
        agent_name_var.set(kwargs['agent'])


def get_context() -> Dict[str, Any]:
    """Get current context as a dictionary."""
    return {
        "request_id": request_id_var.get(),
        "session_id": session_id_var.get(),
        "agent": agent_name_var.get(),
    }


def clear_context():
    """Clear all context variables."""
    request_id_var.set(None)
    session_id_var.set(None)
    agent_name_var.set(None)


# Convenience function to create a logger
def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name
        level: Minimum log level

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, level)
