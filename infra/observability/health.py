"""
NeuroLens Health Checks

Readiness and liveness probes for Kubernetes deployments.
Checks database, cache, model loader, and other dependencies.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
import time


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0.0
    details: dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": round(self.latency_ms, 2),
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class OverallHealth:
    """Overall system health status."""
    status: HealthStatus
    checks: list[HealthCheckResult]
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": self.timestamp.isoformat(),
            "checks": [c.to_dict() for c in self.checks],
        }


class HealthChecker:
    """
    Health checker with support for multiple probes.
    
    Supports:
    - Liveness probes (is the service running?)
    - Readiness probes (can the service handle requests?)
    - Startup probes (has the service finished initializing?)
    """
    
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.start_time = time.time()
        self._checks: dict[str, Callable] = {}
        self._async_checks: dict[str, Callable] = {}
        self._startup_complete = False
    
    def register_check(
        self,
        name: str,
        check: Callable[[], HealthCheckResult],
        is_async: bool = False,
    ) -> None:
        """
        Register a health check.
        
        Args:
            name: Check name
            check: Check function returning HealthCheckResult
            is_async: Whether the check is async
        """
        if is_async:
            self._async_checks[name] = check
        else:
            self._checks[name] = check
    
    def mark_startup_complete(self) -> None:
        """Mark startup as complete for startup probes."""
        self._startup_complete = True
    
    def _run_check(self, name: str, check: Callable) -> HealthCheckResult:
        """Run a single synchronous health check."""
        start = time.perf_counter()
        try:
            result = check()
            result.latency_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    async def _run_async_check(self, name: str, check: Callable) -> HealthCheckResult:
        """Run a single async health check."""
        start = time.perf_counter()
        try:
            result = await check()
            result.latency_ms = (time.perf_counter() - start) * 1000
            return result
        except Exception as e:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )
    
    async def check_all(self) -> OverallHealth:
        """Run all health checks and return overall status."""
        results: list[HealthCheckResult] = []
        
        # Run sync checks
        for name, check in self._checks.items():
            result = self._run_check(name, check)
            results.append(result)
        
        # Run async checks concurrently
        if self._async_checks:
            async_results = await asyncio.gather(
                *[
                    self._run_async_check(name, check)
                    for name, check in self._async_checks.items()
                ],
                return_exceptions=True,
            )
            
            for i, (name, _) in enumerate(self._async_checks.items()):
                result = async_results[i]
                if isinstance(result, Exception):
                    result = HealthCheckResult(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=str(result),
                    )
                results.append(result)
        
        # Determine overall status
        if any(r.status == HealthStatus.UNHEALTHY for r in results):
            overall_status = HealthStatus.UNHEALTHY
        elif any(r.status == HealthStatus.DEGRADED for r in results):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return OverallHealth(
            status=overall_status,
            checks=results,
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
        )
    
    def liveness(self) -> OverallHealth:
        """
        Liveness probe - minimal check that service is running.
        
        Used by Kubernetes to determine if the pod should be restarted.
        """
        return OverallHealth(
            status=HealthStatus.HEALTHY,
            checks=[
                HealthCheckResult(
                    name="liveness",
                    status=HealthStatus.HEALTHY,
                    message="Service is alive",
                )
            ],
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
        )
    
    async def readiness(self) -> OverallHealth:
        """
        Readiness probe - check that service can handle requests.
        
        Used by Kubernetes to determine if traffic should be sent to the pod.
        """
        return await self.check_all()
    
    def startup(self) -> OverallHealth:
        """
        Startup probe - check that service has finished initializing.
        
        Used by Kubernetes during initial startup.
        """
        status = HealthStatus.HEALTHY if self._startup_complete else HealthStatus.UNHEALTHY
        message = "Startup complete" if self._startup_complete else "Startup in progress"
        
        return OverallHealth(
            status=status,
            checks=[
                HealthCheckResult(
                    name="startup",
                    status=status,
                    message=message,
                )
            ],
            version=self.version,
            uptime_seconds=time.time() - self.start_time,
        )


# Pre-built health check functions

def check_database(get_connection: Callable) -> Callable[[], HealthCheckResult]:
    """
    Create a database health check.
    
    Args:
        get_connection: Function to get database connection
    """
    def check() -> HealthCheckResult:
        try:
            conn = get_connection()
            # Execute a simple query
            conn.execute("SELECT 1")
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection OK",
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {e}",
            )
    
    return check


def check_redis(get_client: Callable) -> Callable[[], HealthCheckResult]:
    """
    Create a Redis health check.
    
    Args:
        get_client: Function to get Redis client
    """
    def check() -> HealthCheckResult:
        try:
            client = get_client()
            client.ping()
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection OK",
            )
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {e}",
            )
    
    return check


def check_model_loader(get_models: Callable) -> Callable[[], HealthCheckResult]:
    """
    Create a model loader health check.
    
    Args:
        get_models: Function to get loaded models
    """
    def check() -> HealthCheckResult:
        try:
            models = get_models()
            if not models:
                return HealthCheckResult(
                    name="model_loader",
                    status=HealthStatus.DEGRADED,
                    message="No models loaded",
                    details={"model_count": 0},
                )
            return HealthCheckResult(
                name="model_loader",
                status=HealthStatus.HEALTHY,
                message=f"{len(models)} models loaded",
                details={"model_count": len(models), "models": list(models.keys())},
            )
        except Exception as e:
            return HealthCheckResult(
                name="model_loader",
                status=HealthStatus.UNHEALTHY,
                message=f"Model loader check failed: {e}",
            )
    
    return check


def check_disk_space(
    path: str = "/",
    warning_threshold: float = 0.8,
    critical_threshold: float = 0.9,
) -> Callable[[], HealthCheckResult]:
    """
    Create a disk space health check.
    
    Args:
        path: Path to check
        warning_threshold: Usage ratio for degraded status
        critical_threshold: Usage ratio for unhealthy status
    """
    def check() -> HealthCheckResult:
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            usage_ratio = used / total
            
            details = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round(usage_ratio * 100, 1),
            }
            
            if usage_ratio >= critical_threshold:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Disk usage critical: {details['usage_percent']}%",
                    details=details,
                )
            elif usage_ratio >= warning_threshold:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.DEGRADED,
                    message=f"Disk usage warning: {details['usage_percent']}%",
                    details=details,
                )
            else:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.HEALTHY,
                    message=f"Disk usage OK: {details['usage_percent']}%",
                    details=details,
                )
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {e}",
            )
    
    return check


def check_memory(
    warning_threshold: float = 0.8,
    critical_threshold: float = 0.9,
) -> Callable[[], HealthCheckResult]:
    """
    Create a memory usage health check.
    
    Args:
        warning_threshold: Usage ratio for degraded status
        critical_threshold: Usage ratio for unhealthy status
    """
    def check() -> HealthCheckResult:
        try:
            import psutil
            memory = psutil.virtual_memory()
            usage_ratio = memory.percent / 100
            
            details = {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent,
            }
            
            if usage_ratio >= critical_threshold:
                return HealthCheckResult(
                    name="memory",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Memory usage critical: {memory.percent}%",
                    details=details,
                )
            elif usage_ratio >= warning_threshold:
                return HealthCheckResult(
                    name="memory",
                    status=HealthStatus.DEGRADED,
                    message=f"Memory usage warning: {memory.percent}%",
                    details=details,
                )
            else:
                return HealthCheckResult(
                    name="memory",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage OK: {memory.percent}%",
                    details=details,
                )
        except ImportError:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.DEGRADED,
                message="psutil not installed",
            )
        except Exception as e:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {e}",
            )
    
    return check


# Global health checker instance
health_checker = HealthChecker()
