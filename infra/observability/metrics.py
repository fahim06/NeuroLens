"""
NeuroLens Metrics Collection

Prometheus-compatible metrics for monitoring system health and performance.
Implements Golden Signals: Latency, Traffic, Errors, Saturation.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from functools import wraps
from dataclasses import dataclass, field
from collections import defaultdict
import threading


class MetricType(str, Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Metric value with labels."""
    name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HistogramBucket:
    """Histogram bucket for latency distribution."""
    le: float  # Less than or equal
    count: int = 0


class Counter:
    """Prometheus-style counter metric."""
    
    def __init__(self, name: str, description: str, labels: list[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def inc(self, value: float = 1, **labels: str) -> None:
        """Increment counter."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] += value
    
    def get(self, **labels: str) -> float:
        """Get counter value."""
        label_key = tuple(sorted(labels.items()))
        return self._values.get(label_key, 0)
    
    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        result = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = dict(label_key)
                result.append(MetricValue(
                    name=self.name,
                    metric_type=MetricType.COUNTER,
                    value=value,
                    labels=labels,
                ))
        return result


class Gauge:
    """Prometheus-style gauge metric."""
    
    def __init__(self, name: str, description: str, labels: list[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()
    
    def set(self, value: float, **labels: str) -> None:
        """Set gauge value."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] = value
    
    def inc(self, value: float = 1, **labels: str) -> None:
        """Increment gauge."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] += value
    
    def dec(self, value: float = 1, **labels: str) -> None:
        """Decrement gauge."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._values[label_key] -= value
    
    def get(self, **labels: str) -> float:
        """Get gauge value."""
        label_key = tuple(sorted(labels.items()))
        return self._values.get(label_key, 0)
    
    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        result = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = dict(label_key)
                result.append(MetricValue(
                    name=self.name,
                    metric_type=MetricType.GAUGE,
                    value=value,
                    labels=labels,
                ))
        return result


class Histogram:
    """Prometheus-style histogram metric for latency distribution."""
    
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    
    def __init__(
        self,
        name: str,
        description: str,
        labels: list[str] = None,
        buckets: tuple[float, ...] = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: dict[tuple, dict[float, int]] = defaultdict(lambda: {b: 0 for b in self.buckets})
        self._sums: dict[tuple, float] = defaultdict(float)
        self._totals: dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def observe(self, value: float, **labels: str) -> None:
        """Observe a value."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            self._sums[label_key] += value
            self._totals[label_key] += 1
            for bucket in self.buckets:
                if value <= bucket:
                    self._counts[label_key][bucket] += 1
    
    def time(self, **labels: str):
        """Context manager for timing."""
        return HistogramTimer(self, labels)
    
    def get_percentile(self, percentile: float, **labels: str) -> Optional[float]:
        """Estimate percentile value."""
        label_key = tuple(sorted(labels.items()))
        with self._lock:
            total = self._totals.get(label_key, 0)
            if total == 0:
                return None
            
            target = total * percentile / 100
            cumulative = 0
            
            for bucket in sorted(self.buckets):
                cumulative = self._counts[label_key].get(bucket, 0)
                if cumulative >= target:
                    return bucket
        
        return self.buckets[-1]
    
    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        result = []
        with self._lock:
            for label_key in self._counts.keys():
                labels = dict(label_key)
                
                # Add bucket counts
                for bucket, count in self._counts[label_key].items():
                    result.append(MetricValue(
                        name=f"{self.name}_bucket",
                        metric_type=MetricType.HISTOGRAM,
                        value=count,
                        labels={**labels, "le": str(bucket)},
                    ))
                
                # Add sum and count
                result.append(MetricValue(
                    name=f"{self.name}_sum",
                    metric_type=MetricType.HISTOGRAM,
                    value=self._sums.get(label_key, 0),
                    labels=labels,
                ))
                result.append(MetricValue(
                    name=f"{self.name}_count",
                    metric_type=MetricType.HISTOGRAM,
                    value=self._totals.get(label_key, 0),
                    labels=labels,
                ))
        
        return result


class HistogramTimer:
    """Timer context manager for histogram."""
    
    def __init__(self, histogram: Histogram, labels: dict[str, str]):
        self.histogram = histogram
        self.labels = labels
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        if self.start_time:
            duration = time.perf_counter() - self.start_time
            self.histogram.observe(duration, **self.labels)


class MetricsCollector:
    """Central metrics collector and registry."""
    
    def __init__(self):
        self._metrics: dict[str, Counter | Gauge | Histogram] = {}
        self._lock = threading.Lock()
    
    def counter(
        self,
        name: str,
        description: str,
        labels: list[str] = None,
    ) -> Counter:
        """Create or get a counter metric."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, description, labels)
            return self._metrics[name]
    
    def gauge(
        self,
        name: str,
        description: str,
        labels: list[str] = None,
    ) -> Gauge:
        """Create or get a gauge metric."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, description, labels)
            return self._metrics[name]
    
    def histogram(
        self,
        name: str,
        description: str,
        labels: list[str] = None,
        buckets: tuple[float, ...] = None,
    ) -> Histogram:
        """Create or get a histogram metric."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, description, labels, buckets)
            return self._metrics[name]
    
    def collect_all(self) -> list[MetricValue]:
        """Collect all registered metrics."""
        result = []
        with self._lock:
            for metric in self._metrics.values():
                result.extend(metric.collect())
        return result
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        for metric_value in self.collect_all():
            labels_str = ""
            if metric_value.labels:
                label_parts = [f'{k}="{v}"' for k, v in metric_value.labels.items()]
                labels_str = "{" + ",".join(label_parts) + "}"
            
            lines.append(f"{metric_value.name}{labels_str} {metric_value.value}")
        
        return "\n".join(lines)


# Global metrics collector
metrics = MetricsCollector()

# Pre-defined metrics for NeuroLens

# API Metrics
http_requests_total = metrics.counter(
    "neurolens_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = metrics.histogram(
    "neurolens_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

http_requests_in_progress = metrics.gauge(
    "neurolens_http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Inference Metrics
inference_requests_total = metrics.counter(
    "neurolens_inference_requests_total",
    "Total inference requests",
    ["model", "status"],
)

inference_duration_seconds = metrics.histogram(
    "neurolens_inference_duration_seconds",
    "Inference request latency",
    ["model"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

inference_batch_size = metrics.histogram(
    "neurolens_inference_batch_size",
    "Inference batch sizes",
    ["model"],
    buckets=(1, 2, 4, 8, 16, 32, 64, 128),
)

inference_queue_size = metrics.gauge(
    "neurolens_inference_queue_size",
    "Inference queue size",
    ["model"],
)

# Model Metrics
model_load_duration_seconds = metrics.histogram(
    "neurolens_model_load_duration_seconds",
    "Model loading time",
    ["model"],
)

model_memory_bytes = metrics.gauge(
    "neurolens_model_memory_bytes",
    "Model memory usage",
    ["model"],
)

models_loaded = metrics.gauge(
    "neurolens_models_loaded",
    "Number of models currently loaded",
)

# System Metrics
cpu_usage_percent = metrics.gauge(
    "neurolens_cpu_usage_percent",
    "CPU usage percentage",
)

memory_usage_bytes = metrics.gauge(
    "neurolens_memory_usage_bytes",
    "Memory usage in bytes",
)

gpu_usage_percent = metrics.gauge(
    "neurolens_gpu_usage_percent",
    "GPU usage percentage",
    ["device"],
)

gpu_memory_bytes = metrics.gauge(
    "neurolens_gpu_memory_bytes",
    "GPU memory usage in bytes",
    ["device"],
)

# Job Metrics
training_jobs_total = metrics.counter(
    "neurolens_training_jobs_total",
    "Total training jobs",
    ["status"],
)

training_duration_seconds = metrics.histogram(
    "neurolens_training_duration_seconds",
    "Training job duration",
    ["model_type"],
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400),
)

# Error Metrics
errors_total = metrics.counter(
    "neurolens_errors_total",
    "Total errors",
    ["type", "component"],
)


def timed(metric: Histogram, **static_labels):
    """Decorator for timing function execution."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with metric.time(**static_labels):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                metric.observe(duration, **static_labels)
        
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


def asyncio_iscoroutinefunction(func: Callable) -> bool:
    """Check if function is async."""
    import asyncio
    return asyncio.iscoroutinefunction(func)
