"""
Health Check Endpoints

Purpose:
- Liveness probe for Kubernetes/Docker
- CI/CD validation
- Load balancer health checks

Rules:
- No business logic
- No ML imports
- No database logic
"""

from fastapi import APIRouter, status

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Basic health check endpoint for liveness probes",
    response_description="Returns status: ok if the service is healthy",
)
async def health_check() -> dict[str, str]:
    """
    Basic health check.

    Returns:
        dict: {"status": "ok"}
    """
    return {"status": "ok"}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Readiness probe to verify all dependencies are available",
)
async def readiness_check() -> dict[str, str]:
    """
    Readiness probe.

    Verifies that all required dependencies are available.
    Future: Add database, cache, and ML model checks.

    Returns:
        dict: {"status": "ready"}
    """
    # TODO Phase 4+: Add dependency checks
    # - Database connection
    # - ML model availability
    # - Cache connectivity
    return {"status": "ready"}


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Liveness probe to verify the service is running",
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe.

    Simple check to verify the service process is alive.

    Returns:
        dict: {"status": "alive"}
    """
    return {"status": "alive"}
