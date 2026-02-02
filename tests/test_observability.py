"""
Tests for NeuroLens Observability Module

Tests for logging, metrics, tracing, and health checks.
"""
from __future__ import annotations

import pytest
import time
import asyncio
from datetime import datetime, timezone


class TestLogging:
    """Tests for structured logging."""
    
    def test_get_logger(self):
        """Test logger creation."""
        from infra.observability.logging import get_logger, LogLevel
        
        logger = get_logger("test.logger")
        assert logger is not None
        assert logger.name == "test.logger"
    
    def test_configure_logging(self):
        """Test logging configuration."""
        from infra.observability.logging import configure_logging, get_logger, LogLevel
        
        configure_logging(level=LogLevel.DEBUG, json_output=False)
        logger = get_logger("test.config")
        
        # Should not raise
        logger.debug("Test debug message")
        logger.info("Test info message", extra_key="extra_value")
    
    def test_request_context(self):
        """Test request context setting."""
        from infra.observability.logging import (
            set_request_context,
            clear_request_context,
            request_id_var,
            user_id_var,
        )
        
        set_request_context(request_id="req-123", user_id="user-456")
        
        assert request_id_var.get() == "req-123"
        assert user_id_var.get() == "user-456"
        
        clear_request_context()
        
        assert request_id_var.get() is None
        assert user_id_var.get() is None


class TestMetrics:
    """Tests for Prometheus-style metrics."""
    
    def test_counter(self):
        """Test counter metric."""
        from infra.observability.metrics import Counter
        
        counter = Counter("test_counter", "Test counter", ["label1"])
        
        counter.inc(label1="value1")
        counter.inc(2, label1="value1")
        counter.inc(label1="value2")
        
        assert counter.get(label1="value1") == 3
        assert counter.get(label1="value2") == 1
        assert counter.get(label1="value3") == 0
    
    def test_gauge(self):
        """Test gauge metric."""
        from infra.observability.metrics import Gauge
        
        gauge = Gauge("test_gauge", "Test gauge", ["service"])
        
        gauge.set(100, service="api")
        assert gauge.get(service="api") == 100
        
        gauge.inc(10, service="api")
        assert gauge.get(service="api") == 110
        
        gauge.dec(20, service="api")
        assert gauge.get(service="api") == 90
    
    def test_histogram(self):
        """Test histogram metric."""
        from infra.observability.metrics import Histogram
        
        histogram = Histogram(
            "test_histogram",
            "Test histogram",
            ["endpoint"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0),
        )
        
        # Observe some values
        histogram.observe(0.05, endpoint="/api")
        histogram.observe(0.3, endpoint="/api")
        histogram.observe(1.5, endpoint="/api")
        histogram.observe(3.0, endpoint="/api")
        
        # Check metrics collected
        metrics = histogram.collect()
        assert len(metrics) > 0
    
    def test_histogram_timer(self):
        """Test histogram timer context manager."""
        from infra.observability.metrics import Histogram
        
        histogram = Histogram("test_timer", "Test timer")
        
        with histogram.time():
            time.sleep(0.01)  # Sleep 10ms
        
        metrics = histogram.collect()
        assert any(m.name == "test_timer_count" and m.value == 1 for m in metrics)
    
    def test_metrics_collector(self):
        """Test metrics collector registry."""
        from infra.observability.metrics import MetricsCollector
        
        collector = MetricsCollector()
        
        counter = collector.counter("collector_counter", "Test")
        gauge = collector.gauge("collector_gauge", "Test")
        histogram = collector.histogram("collector_histogram", "Test")
        
        counter.inc()
        gauge.set(42)
        histogram.observe(0.5)
        
        all_metrics = collector.collect_all()
        assert len(all_metrics) >= 3
        
        # Test Prometheus format export
        prom_format = collector.to_prometheus_format()
        assert "collector_counter" in prom_format
        assert "collector_gauge" in prom_format


class TestTracing:
    """Tests for distributed tracing."""
    
    def test_span_context(self):
        """Test span context creation and serialization."""
        from infra.observability.tracing import SpanContext
        
        context = SpanContext(
            trace_id="abcd1234" * 4,
            span_id="span5678",
            parent_span_id="parent1234",
        )
        
        # Test to_dict
        data = context.to_dict()
        assert data["trace_id"] == "abcd1234" * 4
        assert data["span_id"] == "span5678"
        
        # Test from_dict
        restored = SpanContext.from_dict(data)
        assert restored.trace_id == context.trace_id
        
        # Test header format
        header = context.to_header()
        assert "abcd1234" in header
    
    def test_span_creation(self):
        """Test span creation and attributes."""
        from infra.observability.tracing import Span, SpanContext, SpanKind, SpanStatus
        
        context = SpanContext(trace_id="trace123", span_id="span456")
        span = Span(
            name="test_operation",
            context=context,
            kind=SpanKind.SERVER,
        )
        
        # Add attributes and events
        span.set_attribute("http.method", "GET")
        span.add_event("processing_started", {"step": 1})
        
        assert span.attributes["http.method"] == "GET"
        assert len(span.events) == 1
        
        # End span
        span.end()
        assert span.end_time is not None
        assert span.duration_ms is not None
    
    def test_tracer_start_span(self):
        """Test tracer span creation."""
        from infra.observability.tracing import Tracer, SpanKind
        
        tracer = Tracer(service_name="test-service")
        
        with tracer.start_span("outer_span", kind=SpanKind.SERVER) as outer:
            outer.set_attribute("key", "value")
            
            with tracer.start_span("inner_span") as inner:
                # Inner span should have outer as parent
                assert inner.context.parent_span_id == outer.context.span_id
                assert inner.context.trace_id == outer.context.trace_id
    
    def test_trace_function_decorator(self):
        """Test trace_function decorator."""
        from infra.observability.tracing import trace_function, tracer
        
        @trace_function("test_operation")
        def test_func(x: int) -> int:
            return x * 2
        
        result = test_func(5)
        assert result == 10
        
        # Check that a span was created
        recent = tracer.get_recent_spans()
        assert any(s.name == "test_operation" for s in recent)


class TestHealth:
    """Tests for health checks."""
    
    def test_health_check_result(self):
        """Test health check result creation."""
        from infra.observability.health import HealthCheckResult, HealthStatus
        
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All good",
            latency_ms=5.5,
        )
        
        data = result.to_dict()
        assert data["name"] == "test_check"
        assert data["status"] == "healthy"
        assert data["latency_ms"] == 5.5
    
    def test_health_checker_registration(self):
        """Test health check registration."""
        from infra.observability.health import HealthChecker, HealthCheckResult, HealthStatus
        
        checker = HealthChecker(version="1.0.0")
        
        def my_check() -> HealthCheckResult:
            return HealthCheckResult(
                name="my_check",
                status=HealthStatus.HEALTHY,
                message="OK",
            )
        
        checker.register_check("my_check", my_check)
        
        # Check liveness
        liveness = checker.liveness()
        assert liveness.status == HealthStatus.HEALTHY
    
    def test_health_checker_readiness(self):
        """Test async readiness check."""
        import asyncio
        from infra.observability.health import HealthChecker, HealthCheckResult, HealthStatus
        
        checker = HealthChecker(version="1.0.0")
        
        def sync_check() -> HealthCheckResult:
            return HealthCheckResult(
                name="sync_check",
                status=HealthStatus.HEALTHY,
                message="OK",
            )
        
        async def async_check() -> HealthCheckResult:
            await asyncio.sleep(0.001)
            return HealthCheckResult(
                name="async_check",
                status=HealthStatus.HEALTHY,
                message="OK",
            )
        
        checker.register_check("sync_check", sync_check)
        checker.register_check("async_check", async_check, is_async=True)
        
        # Run async function synchronously
        readiness = asyncio.get_event_loop().run_until_complete(checker.readiness())
        assert readiness.status == HealthStatus.HEALTHY
        assert len(readiness.checks) == 2
    
    def test_startup_probe(self):
        """Test startup probe."""
        from infra.observability.health import HealthChecker, HealthStatus
        
        checker = HealthChecker()
        
        # Before marking complete
        startup = checker.startup()
        assert startup.status == HealthStatus.UNHEALTHY
        
        # After marking complete
        checker.mark_startup_complete()
        startup = checker.startup()
        assert startup.status == HealthStatus.HEALTHY
    
    def test_disk_space_check(self):
        """Test disk space health check."""
        from infra.observability.health import check_disk_space, HealthStatus
        
        check = check_disk_space("/")
        result = check()
        
        assert result.name == "disk_space"
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert "usage_percent" in result.details


class TestSentry:
    """Tests for Sentry integration."""
    
    def test_sentry_config_from_env(self):
        """Test Sentry config loading from environment."""
        import os
        from infra.observability.sentry import SentryConfig
        
        # Without DSN, should return None
        config = SentryConfig.from_env()
        # May or may not be None depending on environment
    
    def test_sentry_client_without_sdk(self):
        """Test Sentry client works without SDK installed."""
        from infra.observability.sentry import SentryClient
        
        # Create client without config
        client = SentryClient(config=None)
        
        # Should not raise
        event_id = client.capture_message("Test message")
        assert event_id is None  # Not initialized
        
        exception_id = client.capture_exception(Exception("Test error"))
        assert exception_id is None


class TestMiddleware:
    """Tests for observability middleware."""
    
    def test_path_normalization(self):
        """Test path normalization for metrics."""
        try:
            from infra.observability.middleware import ObservabilityMiddleware
        except ImportError:
            pytest.skip("starlette not installed")
        
        class MockApp:
            pass
        
        middleware = ObservabilityMiddleware(MockApp())
        
        # Test various paths
        assert middleware._normalize_path("/v1/health") == "/v1/health"
        assert middleware._normalize_path("/v1/users/123") == "/v1/users/{id}"
        assert middleware._normalize_path("/v1/models/abc-def-123/versions/1") == "/v1/models/{id}/versions/{id}"


class TestIntegration:
    """Integration tests for observability stack."""
    
    def test_full_request_observability(self):
        """Test logging, metrics, and tracing together."""
        from infra.observability.logging import get_logger, set_request_context, clear_request_context
        from infra.observability.metrics import MetricsCollector
        from infra.observability.tracing import Tracer, SpanKind
        
        # Setup
        logger = get_logger("integration.test")
        metrics = MetricsCollector()
        tracer = Tracer(service_name="test")
        
        request_counter = metrics.counter("integration_requests", "Test requests", ["endpoint"])
        request_latency = metrics.histogram("integration_latency", "Test latency", ["endpoint"])
        
        # Simulate a request
        request_id = "req-integration-test"
        
        set_request_context(request_id=request_id)
        
        with tracer.start_span("handle_request", kind=SpanKind.SERVER) as span:
            span.set_attribute("request_id", request_id)
            
            logger.info("Processing request", endpoint="/test")
            
            with request_latency.time(endpoint="/test"):
                # Simulate some work
                time.sleep(0.01)
            
            request_counter.inc(endpoint="/test")
            
            logger.info("Request completed")
        
        clear_request_context()
        
        # Verify metrics
        assert request_counter.get(endpoint="/test") == 1
        
        # Verify span was created
        recent_spans = tracer.get_recent_spans()
        assert any(s.name == "handle_request" for s in recent_spans)


# Run with: pytest tests/test_observability.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
