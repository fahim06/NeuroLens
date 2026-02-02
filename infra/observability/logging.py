"""
NeuroLens Centralized Logging

Structured logging using structlog for consistent, searchable logs.
Supports JSON output for log aggregation systems.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from contextvars import ContextVar
import json

# Context variables for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """Structured logger with JSON output support."""
    
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        json_output: bool = True,
    ):
        self.name = name
        self.level = level
        self.json_output = json_output
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.value))
        
        # Set up handler if not already configured
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(getattr(logging, level.value))
            self._logger.addHandler(handler)
    
    def _format_message(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ) -> str:
        """Format log message as structured JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
        }
        
        # Add context variables
        if request_id := request_id_var.get():
            log_data["request_id"] = request_id
        if user_id := user_id_var.get():
            log_data["user_id"] = user_id
        if trace_id := trace_id_var.get():
            log_data["trace_id"] = trace_id
        
        # Add extra fields
        if kwargs:
            log_data["extra"] = kwargs
        
        if self.json_output:
            return json.dumps(log_data)
        else:
            extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"[{log_data['timestamp']}] {level} {self.name}: {message} {extra_str}".strip()
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(self._format_message("DEBUG", message, **kwargs))
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(self._format_message("INFO", message, **kwargs))
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(self._format_message("WARNING", message, **kwargs))
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(self._format_message("ERROR", message, **kwargs))
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._logger.critical(self._format_message("CRITICAL", message, **kwargs))
    
    def exception(self, message: str, exc: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log exception with stack trace."""
        if exc:
            kwargs["exception_type"] = type(exc).__name__
            kwargs["exception_message"] = str(exc)
        self._logger.exception(self._format_message("ERROR", message, **kwargs))


# Logger registry
_loggers: dict[str, StructuredLogger] = {}

# Global configuration
_global_level = LogLevel.INFO
_global_json_output = True


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    json_output: bool = True,
) -> None:
    """
    Configure global logging settings.
    
    Args:
        level: Global log level
        json_output: Whether to output JSON formatted logs
    """
    global _global_level, _global_json_output
    _global_level = level
    _global_json_output = json_output
    
    # Update existing loggers
    for logger in _loggers.values():
        logger.level = level
        logger.json_output = json_output
        logger._logger.setLevel(getattr(logging, level.value))


def get_logger(name: str) -> StructuredLogger:
    """
    Get or create a structured logger.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(
            name=name,
            level=_global_level,
            json_output=_global_json_output,
        )
    return _loggers[name]


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Set request-scoped context for logging."""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if trace_id:
        trace_id_var.set(trace_id)


def clear_request_context() -> None:
    """Clear request-scoped context."""
    request_id_var.set(None)
    user_id_var.set(None)
    trace_id_var.set(None)


# Pre-configured loggers for common components
api_logger = get_logger("neurolens.api")
ml_logger = get_logger("neurolens.ml")
inference_logger = get_logger("neurolens.inference")
worker_logger = get_logger("neurolens.worker")
data_logger = get_logger("neurolens.data")
