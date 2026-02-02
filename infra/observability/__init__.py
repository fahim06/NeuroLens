"""
NeuroLens Observability Module

Centralized observability infrastructure including:
- Structured logging
- Prometheus metrics
- OpenTelemetry tracing
- Error tracking (Sentry)
- Health checks
- Middleware integration
"""

from infra.observability.logging import (
    get_logger,
    configure_logging,
    LogLevel,
    set_request_context,
    clear_request_context,
    api_logger,
    ml_logger,
    inference_logger,
)
from infra.observability.metrics import (
    metrics,
    MetricsCollector,
    Counter,
    Gauge,
    Histogram,
    http_requests_total,
    http_request_duration_seconds,
    inference_requests_total,
    inference_duration_seconds,
)
from infra.observability.tracing import (
    tracer,
    Tracer,
    TracingMiddleware,
    trace_function,
    Span,
    SpanContext,
    SpanKind,
    SpanStatus,
)
from infra.observability.health import (
    health_checker,
    HealthChecker,
    HealthStatus,
    HealthCheckResult,
    OverallHealth,
    check_database,
    check_redis,
    check_model_loader,
    check_disk_space,
    check_memory,
)
from infra.observability.sentry import (
    sentry,
    SentryClient,
    SentryConfig,
    SentryLevel,
    capture_errors,
)

# Optional imports - may not be available in all environments
try:
    from infra.observability.middleware import (
        ObservabilityMiddleware,
        create_observability_middleware,
    )
except ImportError:
    ObservabilityMiddleware = None
    create_observability_middleware = None

__all__ = [
    # Logging
    "get_logger",
    "configure_logging",
    "LogLevel",
    "set_request_context",
    "clear_request_context",
    "api_logger",
    "ml_logger",
    "inference_logger",
    # Metrics
    "metrics",
    "MetricsCollector",
    "Counter",
    "Gauge",
    "Histogram",
    "http_requests_total",
    "http_request_duration_seconds",
    "inference_requests_total",
    "inference_duration_seconds",
    # Tracing
    "tracer",
    "Tracer",
    "TracingMiddleware",
    "trace_function",
    "Span",
    "SpanContext",
    "SpanKind",
    "SpanStatus",
    # Health
    "health_checker",
    "HealthChecker",
    "HealthStatus",
    "HealthCheckResult",
    "OverallHealth",
    "check_database",
    "check_redis",
    "check_model_loader",
    "check_disk_space",
    "check_memory",
    # Sentry
    "sentry",
    "SentryClient",
    "SentryConfig",
    "SentryLevel",
    "capture_errors",
    # Middleware
    "ObservabilityMiddleware",
    "create_observability_middleware",
]
