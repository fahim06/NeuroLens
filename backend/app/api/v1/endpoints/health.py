"""
Health Check Endpoints

Provides health and readiness endpoints for monitoring and orchestration.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, status

from app.core.config import settings

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Basic health check endpoint",
)
async def health_check() -> dict[str, Any]:
    """
    Basic health check.
    
    Returns:
        Health status with timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version,
    }


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the service is ready to accept requests",
)
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check for Kubernetes/orchestration.
    
    Checks:
        - Application is initialized
        - Dependencies are available (future: DB, ML models)
    
    Returns:
        Readiness status with component checks
    """
    # TODO: Add actual dependency checks (DB, ML models, etc.)
    checks = {
        "api": True,
        "ml_core": True,  # Placeholder
        "storage": True,   # Placeholder
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Check if the service is alive",
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness check for Kubernetes/orchestration.
    
    Returns:
        Simple alive status
    """
    return {"status": "alive"}
