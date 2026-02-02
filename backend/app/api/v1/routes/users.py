"""
NeuroLens Users API Routes

Endpoints for user management.
"""

from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from pydantic import BaseModel, Field

from app.services.users import users_service, UserNotFoundError, UserExistsError
from app.services.auth import auth_service, AuthenticationError
from app.models.user import UserUpdate, UserResponse, UserRole, UserStatus


router = APIRouter(prefix="/users", tags=["Users"])


# Request/Response Schemas

class UpdateUserRequest(BaseModel):
    """Update user request."""
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None


class UserListResponse(BaseModel):
    """User list response."""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Dependency to get current user

async def get_current_user(authorization: str = Header(..., description="Bearer token")):
    """Get current authenticated user."""
    try:
        token = authorization.replace("Bearer ", "")
        return await auth_service.get_current_user(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Routes

@router.get("", response_model=UserListResponse)
async def list_users(
    org_id: Optional[str] = Query(None, description="Filter by organization"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Pagination limit"),
    current_user=Depends(get_current_user),
):
    """
    List users with optional filters.
    
    Requires admin role to list all users.
    Non-admin users can only list users in their organization.
    """
    # Non-admin can only see their org
    if current_user.role != UserRole.ADMIN:
        org_id = current_user.org_id
    
    users = await users_service.list(
        org_id=org_id,
        role=role,
        status=status,
        skip=skip,
        limit=limit,
    )
    total = await users_service.count(org_id=org_id)
    
    return UserListResponse(
        users=[
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                full_name=u.full_name,
                role=u.role,
                status=u.status,
                email_verified=u.email_verified,
                org_id=u.org_id,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get user by ID.
    
    Users can only access their own profile unless they are admin.
    """
    # Check access
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        # Check if same org
        try:
            user = await users_service.get(user_id)
            if user.org_id != current_user.org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        except UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    
    try:
        user = await users_service.get(user_id)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            email_verified=user.email_verified,
            org_id=user.org_id,
            created_at=user.created_at,
            last_login=user.last_login,
            avatar_url=user.avatar_url,
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user=Depends(get_current_user),
):
    """
    Update user profile.
    
    Users can only update their own profile unless they are admin.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    try:
        update_data = UserUpdate(**request.model_dump(exclude_unset=True))
        user = await users_service.update(user_id, update_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            email_verified=user.email_verified,
            org_id=user.org_id,
            created_at=user.created_at,
            avatar_url=user.avatar_url,
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete (deactivate) user.
    
    Users can only delete their own account unless they are admin.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    try:
        await users_service.delete(user_id)
        return MessageResponse(message="User deleted successfully")
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user=Depends(get_current_user),
):
    """
    Update user role.
    
    Admin only endpoint.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    try:
        update_data = UserUpdate(role=role)
        user = await users_service.update(user_id, update_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            email_verified=user.email_verified,
            org_id=user.org_id,
            created_at=user.created_at,
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
