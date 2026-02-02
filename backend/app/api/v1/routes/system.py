"""
System Information Endpoints

Purpose:
- API metadata
- Version reporting
- Environment information

Rules:
- No business logic
- No ML imports
- No database logic
"""

from fastapi import APIRouter, status

from app.core.config import settings

router = APIRouter(prefix="/system", tags=["System"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="System Information",
    description="Returns API metadata and version information",
)
async def system_info() -> dict[str, str]:
    """
    Get system information.

    Returns:
        dict: API name, version, and environment
    """
    return {
        "name": "NeuroLens API",
        "version": "v1",
        "environment": settings.app_env,
    }


@router.get(
    "/version",
    status_code=status.HTTP_200_OK,
    summary="API Version",
    description="Returns detailed version information",
)
async def version_info() -> dict[str, str]:
    """
    Get detailed version information.

    Returns:
        dict: Detailed version info
    """
    return {
        "api_version": "v1",
        "app_version": settings.app_version,
        "app_name": settings.app_name,
    }


@router.get(
    "/config",
    status_code=status.HTTP_200_OK,
    summary="Public Configuration",
    description="Returns non-sensitive configuration values",
)
async def public_config() -> dict[str, str | bool | list[str]]:
    """
    Get public (non-sensitive) configuration.

    Returns:
        dict: Public configuration values
    """
    return {
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "debug": settings.app_debug,
        "allowed_origins": settings.cors_origins,
    }
