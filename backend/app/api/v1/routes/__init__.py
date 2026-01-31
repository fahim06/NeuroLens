"""
API v1 Routes

Phase 2: Health and System routes only.
No ML imports. No database logic.
"""

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.system import router as system_router

__all__ = ["health_router", "system_router"]
