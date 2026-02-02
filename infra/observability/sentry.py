"""
NeuroLens Sentry Integration

Error tracking and performance monitoring with Sentry.
Optional integration - gracefully handles missing Sentry SDK.
"""
from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class SentryLevel(str, Enum):
    """Sentry severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class SentryConfig:
    """Sentry configuration."""
    dsn: str
    environment: str = "development"
    release: Optional[str] = None
    traces_sample_rate: float = 0.1
    profiles_sample_rate: float = 0.1
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> Optional[SentryConfig]:
        """Load configuration from environment variables."""
        dsn = os.getenv("SENTRY_DSN")
        if not dsn:
            return None
        
        return cls(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
            release=os.getenv("SENTRY_RELEASE"),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            debug=os.getenv("SENTRY_DEBUG", "").lower() == "true",
        )


class SentryClient:
    """
    Sentry client wrapper.
    
    Provides a consistent interface even when Sentry SDK is not installed.
    """
    
    def __init__(self, config: Optional[SentryConfig] = None):
        self.config = config
        self._sentry = None
        self._initialized = False
        
        if config:
            self._initialize()
    
    def _initialize(self) -> bool:
        """Initialize Sentry SDK."""
        if self._initialized:
            return True
        
        if not self.config:
            return False
        
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.starlette import StarletteIntegration
            
            sentry_sdk.init(
                dsn=self.config.dsn,
                environment=self.config.environment,
                release=self.config.release,
                traces_sample_rate=self.config.traces_sample_rate,
                profiles_sample_rate=self.config.profiles_sample_rate,
                debug=self.config.debug,
                integrations=[
                    StarletteIntegration(),
                    FastApiIntegration(),
                ],
            )
            
            self._sentry = sentry_sdk
            self._initialized = True
            return True
            
        except ImportError:
            # Sentry SDK not installed
            return False
        except Exception as e:
            print(f"Failed to initialize Sentry: {e}")
            return False
    
    def capture_exception(
        self,
        exception: Exception,
        tags: dict[str, str] = None,
        extras: dict[str, Any] = None,
        level: SentryLevel = SentryLevel.ERROR,
    ) -> Optional[str]:
        """
        Capture an exception.
        
        Args:
            exception: The exception to capture
            tags: Tags to attach to the event
            extras: Extra context data
            level: Severity level
            
        Returns:
            Event ID if captured, None otherwise
        """
        if not self._sentry:
            return None
        
        with self._sentry.push_scope() as scope:
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            if extras:
                for key, value in extras.items():
                    scope.set_extra(key, value)
            scope.level = level.value
            
            return self._sentry.capture_exception(exception)
    
    def capture_message(
        self,
        message: str,
        level: SentryLevel = SentryLevel.INFO,
        tags: dict[str, str] = None,
        extras: dict[str, Any] = None,
    ) -> Optional[str]:
        """
        Capture a message.
        
        Args:
            message: The message to capture
            level: Severity level
            tags: Tags to attach to the event
            extras: Extra context data
            
        Returns:
            Event ID if captured, None otherwise
        """
        if not self._sentry:
            return None
        
        with self._sentry.push_scope() as scope:
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            if extras:
                for key, value in extras.items():
                    scope.set_extra(key, value)
            scope.level = level.value
            
            return self._sentry.capture_message(message)
    
    def set_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> None:
        """Set user context."""
        if not self._sentry:
            return
        
        self._sentry.set_user({
            "id": user_id,
            "email": email,
            "username": username,
        })
    
    def set_tag(self, key: str, value: str) -> None:
        """Set a global tag."""
        if not self._sentry:
            return
        
        self._sentry.set_tag(key, value)
    
    def set_context(self, name: str, data: dict[str, Any]) -> None:
        """Set context data."""
        if not self._sentry:
            return
        
        self._sentry.set_context(name, data)
    
    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: SentryLevel = SentryLevel.INFO,
        data: dict[str, Any] = None,
    ) -> None:
        """Add a breadcrumb for debugging."""
        if not self._sentry:
            return
        
        self._sentry.add_breadcrumb(
            message=message,
            category=category,
            level=level.value,
            data=data or {},
        )
    
    def start_transaction(
        self,
        name: str,
        op: str = "http.server",
    ):
        """Start a Sentry transaction."""
        if not self._sentry:
            return NullTransaction()
        
        return self._sentry.start_transaction(name=name, op=op)
    
    def start_span(self, op: str, description: str = None):
        """Start a Sentry span."""
        if not self._sentry:
            return NullSpan()
        
        return self._sentry.start_span(op=op, description=description)


class NullTransaction:
    """Null object for transactions when Sentry is not available."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def finish(self):
        pass
    
    def set_tag(self, key, value):
        pass
    
    def set_data(self, key, value):
        pass


class NullSpan:
    """Null object for spans when Sentry is not available."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def finish(self):
        pass
    
    def set_tag(self, key, value):
        pass
    
    def set_data(self, key, value):
        pass


def capture_errors(
    sentry_client: SentryClient,
    tags: dict[str, str] = None,
    reraise: bool = True,
):
    """
    Decorator to capture errors with Sentry.
    
    Args:
        sentry_client: Sentry client instance
        tags: Tags to attach to captured errors
        reraise: Whether to re-raise the exception
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                sentry_client.capture_exception(e, tags=tags)
                if reraise:
                    raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                sentry_client.capture_exception(e, tags=tags)
                if reraise:
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


# Initialize global Sentry client from environment
sentry_config = SentryConfig.from_env()
sentry = SentryClient(sentry_config)
