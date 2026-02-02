"""
NeuroLens Observability Middleware

FastAPI middleware for automatic request/response observability.
Integrates logging, metrics, and tracing into the request lifecycle.
"""
from __future__ import annotations

import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from infra.observability.logging import (
    get_logger,
    set_request_context,
    clear_request_context,
)
from infra.observability.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress,
)
from infra.observability.tracing import (
    tracer,
    SpanKind,
    SpanStatus,
    SpanContext,
)


logger = get_logger("neurolens.middleware")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds observability to all requests.
    
    Features:
    - Request ID generation and propagation
    - Structured logging with request context
    - Prometheus metrics collection
    - Distributed tracing with span creation
    """
    
    def __init__(self, app, service_name: str = "neurolens-api"):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Extract trace context from headers
        traceparent = request.headers.get("traceparent", "")
        parent_context = SpanContext.from_header(traceparent)
        
        # Set request context for logging
        set_request_context(
            request_id=request_id,
            trace_id=parent_context.trace_id if parent_context else None,
        )
        
        # Extract endpoint for metrics
        method = request.method
        path = request.url.path
        endpoint = self._normalize_path(path)
        
        # Track in-progress requests
        http_requests_in_progress.inc(method=method, endpoint=endpoint)
        
        # Start timing
        start_time = time.perf_counter()
        status_code = 500
        
        # Start trace span
        span_name = f"{method} {endpoint}"
        
        try:
            with tracer.start_span(
                span_name,
                kind=SpanKind.SERVER,
                parent=parent_context,
            ) as span:
                # Add request attributes
                span.set_attribute("http.method", method)
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.route", endpoint)
                span.set_attribute("http.request_id", request_id)
                span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
                
                # Log request start
                logger.info(
                    "Request started",
                    method=method,
                    path=path,
                    endpoint=endpoint,
                )
                
                # Process request
                response = await call_next(request)
                status_code = response.status_code
                
                # Add response attributes
                span.set_attribute("http.status_code", status_code)
                
                # Set span status based on HTTP status
                if status_code < 400:
                    span.set_status(SpanStatus.OK)
                else:
                    span.set_status(SpanStatus.ERROR, f"HTTP {status_code}")
                
                # Add trace headers to response
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Trace-ID"] = span.context.trace_id
                
                return response
                
        except Exception as e:
            status_code = 500
            logger.exception(
                "Request failed with exception",
                method=method,
                path=path,
                error=str(e),
            )
            raise
            
        finally:
            # Calculate duration
            duration = time.perf_counter() - start_time
            
            # Record metrics
            http_requests_total.inc(
                method=method,
                endpoint=endpoint,
                status=str(status_code),
            )
            http_request_duration_seconds.observe(
                duration,
                method=method,
                endpoint=endpoint,
            )
            http_requests_in_progress.dec(method=method, endpoint=endpoint)
            
            # Log request completion
            logger.info(
                "Request completed",
                method=method,
                path=path,
                endpoint=endpoint,
                status=status_code,
                duration_ms=round(duration * 1000, 2),
            )
            
            # Clear request context
            clear_request_context()
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for metrics (replace variable segments).
        
        Examples:
            /v1/users/123 -> /v1/users/{id}
            /v1/models/abc-def/versions/1 -> /v1/models/{id}/versions/{version}
        """
        segments = path.split("/")
        normalized = []
        
        for i, segment in enumerate(segments):
            if not segment:
                continue
            
            # Check if segment looks like an ID (UUID, number, etc.)
            if self._is_id_segment(segment):
                normalized.append("{id}")
            else:
                normalized.append(segment)
        
        return "/" + "/".join(normalized)
    
    def _is_id_segment(self, segment: str) -> bool:
        """Check if a path segment is likely an ID."""
        # Numeric IDs
        if segment.isdigit():
            return True
        
        # UUID-like segments
        if len(segment) == 36 and segment.count("-") == 4:
            return True
        
        # Short UUIDs or hashes
        if len(segment) >= 8 and segment.replace("-", "").replace("_", "").isalnum():
            # Check if it's mostly alphanumeric with mixed case or numbers
            has_numbers = any(c.isdigit() for c in segment)
            has_letters = any(c.isalpha() for c in segment)
            if has_numbers and has_letters and len(segment) > 6:
                return True
        
        return False


def create_observability_middleware(app, service_name: str = "neurolens-api"):
    """
    Create and attach observability middleware to a FastAPI app.
    
    Usage:
        from fastapi import FastAPI
        from infra.observability.middleware import create_observability_middleware
        
        app = FastAPI()
        create_observability_middleware(app)
    """
    app.add_middleware(ObservabilityMiddleware, service_name=service_name)
    return app
