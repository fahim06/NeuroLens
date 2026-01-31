"""
API v1 Router

Phase 2: Backend API Router
Versioned API routes following the strategy: /api/v1/*

Rules:
- All routes go through version router
- No unversioned endpoints
- No ML imports in Phase 2
- No database logic in Phase 2
"""

from fastapi import APIRouter

from app.api.v1.routes import health_router, system_router

# Create versioned router
router = APIRouter()

# Include route modules
# Phase 2: Health and System only
router.include_router(health_router)
router.include_router(system_router)
