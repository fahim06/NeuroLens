"""
API v1 Router

Phase 9: Product Layer Router
Complete versioned API routes with authentication, RBAC, and quotas.

Routes:
- /auth/* - Authentication (login, register, tokens)
- /users/* - User management
- /orgs/* - Organization management
- /datasets/* - Dataset registry
- /models/* - Model registry
- /inference/* - Protected inference with quotas
- /admin/* - Admin/analytics endpoints
- /health/* - Health checks
- /system/* - System info
"""

from fastapi import APIRouter

from app.api.v1.routes import (
    health_router,
    system_router,
    auth_router,
    users_router,
    orgs_router,
    datasets_router,
    models_router,
    inference_router,
    admin_router,
)

# Create versioned router
router = APIRouter()

# Include route modules
# Core infrastructure
router.include_router(health_router)
router.include_router(system_router)

# Authentication & Authorization
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(orgs_router)

# Product APIs
router.include_router(datasets_router)
router.include_router(models_router)
router.include_router(inference_router)

# Admin
router.include_router(admin_router)
