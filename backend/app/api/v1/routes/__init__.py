"""
API v1 Routes

Phase 9: Complete product layer routes.
Authentication, RBAC, datasets, models, inference, admin.
"""

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.system import router as system_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.orgs import router as orgs_router
from app.api.v1.routes.datasets import router as datasets_router
from app.api.v1.routes.models import router as models_router
from app.api.v1.routes.inference import router as inference_router
from app.api.v1.routes.admin import router as admin_router

__all__ = [
    "health_router",
    "system_router",
    "auth_router",
    "users_router",
    "orgs_router",
    "datasets_router",
    "models_router",
    "inference_router",
    "admin_router",
]
