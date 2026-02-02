"""
NeuroLens Admin API Routes

Admin endpoints for system management and analytics.
"""

from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from pydantic import BaseModel, Field

from app.services.users import users_service
from app.services.orgs import orgs_service
from app.services.datasets import datasets_service
from app.services.models import models_service
from app.services.quotas import quotas_service, QuotaType
from app.services.auth import auth_service, AuthenticationError
from app.models.user import UserRole, UserStatus
from app.models.organization import OrgPlan


router = APIRouter(prefix="/admin", tags=["Admin"])


# Request/Response Schemas

class SystemStats(BaseModel):
    """System-wide statistics."""
    total_users: int
    active_users: int
    total_organizations: int
    total_datasets: int
    total_models: int
    api_calls_today: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrgStats(BaseModel):
    """Organization statistics."""
    org_id: str
    org_name: str
    plan: str
    member_count: int
    dataset_count: int
    model_count: int
    api_calls_this_month: int
    storage_used_gb: float


class UserActivity(BaseModel):
    """User activity record."""
    user_id: str
    username: str
    email: str
    last_login: Optional[datetime]
    total_api_calls: int
    org_name: Optional[str]


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Dependency to get admin user

async def get_admin_user(authorization: str = Header(..., description="Bearer token")):
    """Get current user and verify admin role."""
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Routes

@router.get("/stats", response_model=SystemStats)
async def get_system_stats(admin_user=Depends(get_admin_user)):
    """
    Get system-wide statistics.
    
    Admin only endpoint.
    """
    total_users = await users_service.count()
    active_users = len(await users_service.list(status=UserStatus.ACTIVE))
    total_orgs = len(await orgs_service.list())
    total_datasets = await datasets_service.count()
    total_models = await models_service.count()
    
    # TODO: Implement actual API call counting
    api_calls_today = 0
    
    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        total_organizations=total_orgs,
        total_datasets=total_datasets,
        total_models=total_models,
        api_calls_today=api_calls_today,
    )


@router.get("/orgs/stats", response_model=List[OrgStats])
async def get_all_org_stats(
    plan: Optional[OrgPlan] = Query(None, description="Filter by plan"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user=Depends(get_admin_user),
):
    """
    Get statistics for all organizations.
    
    Admin only endpoint.
    """
    orgs = await orgs_service.list(skip=skip, limit=limit)
    
    if plan:
        orgs = [o for o in orgs if o.plan == plan]
    
    stats = []
    for org in orgs:
        stats.append(OrgStats(
            org_id=org.id,
            org_name=org.name,
            plan=org.plan.value,
            member_count=org.current_members,
            dataset_count=org.current_datasets,
            model_count=org.current_models,
            api_calls_this_month=org.api_calls_this_month,
            storage_used_gb=org.storage_used_gb,
        ))
    
    return stats


@router.get("/users/activity", response_model=List[UserActivity])
async def get_user_activity(
    org_id: Optional[str] = Query(None, description="Filter by organization"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin_user=Depends(get_admin_user),
):
    """
    Get user activity records.
    
    Admin only endpoint.
    """
    users = await users_service.list(org_id=org_id, skip=skip, limit=limit)
    
    activities = []
    for user in users:
        org_name = None
        if user.org_id:
            try:
                org = await orgs_service.get(user.org_id)
                org_name = org.name
            except Exception:
                pass
        
        activities.append(UserActivity(
            user_id=user.id,
            username=user.username,
            email=user.email,
            last_login=user.last_login,
            total_api_calls=user.total_api_calls,
            org_name=org_name,
        ))
    
    return activities


@router.post("/users/{user_id}/suspend", response_model=MessageResponse)
async def suspend_user(
    user_id: str,
    admin_user=Depends(get_admin_user),
):
    """
    Suspend a user account.
    
    Admin only endpoint.
    """
    from app.models.user import UserUpdate
    
    try:
        await users_service.update(user_id, UserUpdate(status=UserStatus.SUSPENDED))
        return MessageResponse(message=f"User {user_id} suspended")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users/{user_id}/activate", response_model=MessageResponse)
async def activate_user(
    user_id: str,
    admin_user=Depends(get_admin_user),
):
    """
    Activate a suspended user account.
    
    Admin only endpoint.
    """
    from app.models.user import UserUpdate
    
    try:
        await users_service.update(user_id, UserUpdate(status=UserStatus.ACTIVE))
        return MessageResponse(message=f"User {user_id} activated")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/orgs/{org_id}/upgrade", response_model=MessageResponse)
async def upgrade_org_plan(
    org_id: str,
    plan: OrgPlan = Query(..., description="New plan"),
    admin_user=Depends(get_admin_user),
):
    """
    Upgrade organization plan.
    
    Admin only endpoint.
    """
    from app.models.organization import OrgUpdate
    
    try:
        await orgs_service.update(org_id, OrgUpdate(plan=plan))
        
        # Reset quotas for new plan
        await quotas_service.initialize_org_quotas(org_id, plan.value)
        
        return MessageResponse(message=f"Organization {org_id} upgraded to {plan.value}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )


@router.post("/orgs/{org_id}/reset-quota", response_model=MessageResponse)
async def reset_org_quota(
    org_id: str,
    quota_type: Optional[QuotaType] = Query(None, description="Specific quota to reset"),
    admin_user=Depends(get_admin_user),
):
    """
    Reset organization quota.
    
    Admin only endpoint.
    """
    await quotas_service.reset_quota(org_id=org_id, quota_type=quota_type)
    
    quota_name = quota_type.value if quota_type else "all"
    return MessageResponse(message=f"Reset {quota_name} quota for organization {org_id}")


@router.get("/analytics/usage")
async def get_usage_analytics(
    period: str = Query("day", pattern=r"^(hour|day|week|month)$"),
    admin_user=Depends(get_admin_user),
):
    """
    Get usage analytics.
    
    Admin only endpoint.
    """
    # TODO: Implement actual analytics with time series data
    # This is a placeholder response
    return {
        "period": period,
        "metrics": {
            "api_calls": {
                "total": 0,
                "by_org": {},
            },
            "inference_requests": {
                "total": 0,
                "by_model": {},
            },
            "storage_growth_gb": 0,
            "new_users": 0,
            "new_orgs": 0,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def admin_health_check():
    """
    Admin health check with detailed system info.
    
    No auth required for basic health.
    """
    return {
        "status": "healthy",
        "services": {
            "auth": "ok",
            "users": "ok",
            "orgs": "ok",
            "datasets": "ok",
            "models": "ok",
            "quotas": "ok",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
