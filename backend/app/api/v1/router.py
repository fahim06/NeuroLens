"""
API v1 Router

Versioned API routes following the strategy: /api/v1/*
All endpoints are strictly typed with request/response schemas.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, inference, models, training

# Create versioned router
router = APIRouter(prefix="/v1")

# Include endpoint routers
router.include_router(
    health.router,
    prefix="/health",
    tags=["Health"],
)

router.include_router(
    inference.router,
    prefix="/inference",
    tags=["Inference"],
)

router.include_router(
    models.router,
    prefix="/models",
    tags=["Models"],
)

router.include_router(
    training.router,
    prefix="/training",
    tags=["Training"],
)
