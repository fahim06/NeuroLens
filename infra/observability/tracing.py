"""
NeuroLens Distributed Tracing

OpenTelemetry-compatible tracing for request path visibility.
Traces requests from frontend → API → inference.
"""
from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional
import json


class SpanKind(str, Enum):
    """Span kinds following OpenTelemetry spec."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span status codes."""
    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class SpanContext:
    """Span context for propagation."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for propagation."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id or "",
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> SpanContext:
        """Create from dictionary."""
        return cls(
            trace_id=data.get("trace_id", ""),
            span_id=data.get("span_id", ""),
            parent_span_id=data.get("parent_span_id") or None,
        )
    
    def to_header(self) -> str:
        """Convert to traceparent header format."""
        parent = self.parent_span_id or "0" * 16
        return f"00-{self.trace_id}-{self.span_id}-01"
    
    @classmethod
    def from_header(cls, header: str) -> Optional[SpanContext]:
        """Parse traceparent header."""
        if not header:
            return None
        try:
            parts = header.split("-")
            if len(parts) >= 3:
                return cls(
                    trace_id=parts[1],
                    span_id=parts[2],
                    parent_span_id=None,
                )
        except Exception:
            pass
        return None


@dataclass
class Span:
    """A single span in a trace."""
    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.UNSET
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: dict[str, Any] = None) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        })
    
    def set_status(self, status: SpanStatus, description: str = None) -> None:
        """Set span status."""
        self.status = status
        if description:
            self.attributes["status_description"] = description
    
    def record_exception(self, exception: Exception) -> None:
        """Record an exception."""
        self.set_status(SpanStatus.ERROR, str(exception))
        self.add_event("exception", {
            "exception.type": type(exception).__name__,
            "exception.message": str(exception),
        })
    
    def end(self) -> None:
        """End the span."""
        self.end_time = datetime.now(timezone.utc)
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() * 1000
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "name": self.name,
            "trace_id": self.context.trace_id,
            "span_id": self.context.span_id,
            "parent_span_id": self.context.parent_span_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
        }
    
    def to_json(self) -> str:
        """Convert span to JSON."""
        return json.dumps(self.to_dict())


# Context variable for current span
_current_span: ContextVar[Optional[Span]] = ContextVar("current_span", default=None)


class SpanContextManager:
    """Context manager for spans."""
    
    def __init__(self, span: Span, tracer: Tracer):
        self.span = span
        self.tracer = tracer
        self.token = None
    
    def __enter__(self) -> Span:
        self.token = _current_span.set(self.span)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.span.record_exception(exc_val)
        self.span.end()
        self.tracer._export_span(self.span)
        _current_span.reset(self.token)
        return False


class Tracer:
    """Distributed tracer for request path visibility."""
    
    def __init__(self, service_name: str = "neurolens"):
        self.service_name = service_name
        self._spans: list[Span] = []
        self._exporters: list[Callable[[Span], None]] = []
    
    def _generate_id(self, length: int = 16) -> str:
        """Generate a random hex ID."""
        return uuid.uuid4().hex[:length]
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent: Optional[SpanContext] = None,
        attributes: dict[str, Any] = None,
    ) -> SpanContextManager:
        """
        Start a new span.
        
        Args:
            name: Span name
            kind: Span kind
            parent: Parent span context (auto-detected if not provided)
            attributes: Initial attributes
            
        Returns:
            Span context manager
        """
        # Get parent context
        if parent is None:
            current = _current_span.get()
            if current:
                parent = SpanContext(
                    trace_id=current.context.trace_id,
                    span_id=current.context.span_id,
                )
        
        # Create span context
        if parent:
            context = SpanContext(
                trace_id=parent.trace_id,
                span_id=self._generate_id(),
                parent_span_id=parent.span_id,
            )
        else:
            context = SpanContext(
                trace_id=self._generate_id(32),
                span_id=self._generate_id(),
            )
        
        # Create span
        span = Span(
            name=name,
            context=context,
            kind=kind,
            attributes=attributes or {},
        )
        span.set_attribute("service.name", self.service_name)
        
        return SpanContextManager(span, self)
    
    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return _current_span.get()
    
    def add_exporter(self, exporter: Callable[[Span], None]) -> None:
        """Add a span exporter."""
        self._exporters.append(exporter)
    
    def _export_span(self, span: Span) -> None:
        """Export span to all exporters."""
        for exporter in self._exporters:
            try:
                exporter(span)
            except Exception:
                pass  # Don't let exporter errors affect tracing
        
        # Store span (for debugging/testing)
        self._spans.append(span)
    
    def get_recent_spans(self, limit: int = 100) -> list[Span]:
        """Get recent spans for debugging."""
        return self._spans[-limit:]


# Global tracer instance
tracer = Tracer()


# Console exporter for development
def console_exporter(span: Span) -> None:
    """Export spans to console."""
    print(span.to_json())


# In production, you'd add exporters for Jaeger, Zipkin, etc.
# tracer.add_exporter(console_exporter)


def trace_function(name: str = None, kind: SpanKind = SpanKind.INTERNAL):
    """
    Decorator to trace function execution.
    
    Args:
        name: Span name (defaults to function name)
        kind: Span kind
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_span(span_name, kind=kind) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(SpanStatus.OK)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_span(span_name, kind=kind) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(SpanStatus.OK)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


class TracingMiddleware:
    """ASGI middleware for automatic request tracing."""
    
    def __init__(self, app, tracer: Tracer = tracer):
        self.app = app
        self.tracer = tracer
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract trace context from headers
        headers = dict(scope.get("headers", []))
        traceparent = headers.get(b"traceparent", b"").decode()
        parent_context = SpanContext.from_header(traceparent)
        
        # Create request span
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        span_name = f"{method} {path}"
        
        with self.tracer.start_span(
            span_name,
            kind=SpanKind.SERVER,
            parent=parent_context,
        ) as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", path)
            span.set_attribute("http.scheme", scope.get("scheme", "http"))
            
            # Capture response status
            status_code = 500
            
            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message.get("status", 500)
                    span.set_attribute("http.status_code", status_code)
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
                if status_code < 400:
                    span.set_status(SpanStatus.OK)
                else:
                    span.set_status(SpanStatus.ERROR, f"HTTP {status_code}")
            except Exception as e:
                span.record_exception(e)
                raise


# Predefined span names for consistency
class SpanNames:
    """Standard span names for NeuroLens operations."""
    
    # API
    AUTH = "auth"
    AUTH_VALIDATE_TOKEN = "auth.validate_token"
    AUTH_CREATE_TOKEN = "auth.create_token"
    
    # Inference
    INFERENCE = "inference"
    INFERENCE_PREPROCESS = "inference.preprocess"
    INFERENCE_PREDICT = "inference.predict"
    INFERENCE_POSTPROCESS = "inference.postprocess"
    
    # Data
    DATA_LOAD = "data.load"
    DATA_VALIDATE = "data.validate"
    DATA_TRANSFORM = "data.transform"
    
    # Model
    MODEL_LOAD = "model.load"
    MODEL_SAVE = "model.save"
    MODEL_TRAIN = "model.train"
