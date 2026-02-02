"""
NeuroLens Organizations API Routes

Endpoints for organization and team management.
"""

from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from pydantic import BaseModel, EmailStr, Field

from app.services.orgs import orgs_service, OrgNotFoundError, OrgExistsError, OrgLimitError
from app.services.auth import auth_service, AuthenticationError
from app.models.organization import OrgCreate, OrgUpdate, OrgResponse, OrgPlan, OrgStatus


router = APIRouter(prefix="/orgs", tags=["Organizations"])


# Request/Response Schemas

class CreateOrgRequest(BaseModel):
    """Create organization request."""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None


class UpdateOrgRequest(BaseModel):
    """Update organization request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class InviteMemberRequest(BaseModel):
    """Invite member request."""
    email: EmailStr
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class MemberResponse(BaseModel):
    """Organization member response."""
    id: str
    user_id: str
    role: str
    joined_at: datetime
    invited_by: Optional[str] = None


class OrgListResponse(BaseModel):
    """Organization list response."""
    organizations: List[OrgResponse]
    total: int


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

@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: CreateOrgRequest,
    current_user=Depends(get_current_user),
):
    """
    Create a new organization.
    
    The creating user becomes the owner.
    """
    try:
        org_data = OrgCreate(
            name=request.name,
            slug=request.slug,
            description=request.description,
        )
        org = await orgs_service.create(org_data, current_user.id)
        return OrgResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            owner_id=org.owner_id,
            plan=org.plan,
            status=org.status,
            created_at=org.created_at,
            current_members=org.current_members,
            max_members=org.max_members,
        )
    except OrgExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=OrgListResponse)
async def list_organizations(current_user=Depends(get_current_user)):
    """
    List organizations for the current user.
    
    Returns organizations the user is a member of.
    """
    orgs = await orgs_service.list_for_user(current_user.id)
    return OrgListResponse(
        organizations=[
            OrgResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                description=org.description,
                owner_id=org.owner_id,
                plan=org.plan,
                status=org.status,
                created_at=org.created_at,
                current_members=org.current_members,
                max_members=org.max_members,
            )
            for org in orgs
        ],
        total=len(orgs),
    )


@router.get("/{org_id}", response_model=OrgResponse)
async def get_organization(
    org_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get organization details.
    
    User must be a member of the organization.
    """
    # Check membership
    is_member = await orgs_service.is_member(org_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    
    try:
        org = await orgs_service.get(org_id)
        return OrgResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            owner_id=org.owner_id,
            plan=org.plan,
            status=org.status,
            created_at=org.created_at,
            current_members=org.current_members,
            max_members=org.max_members,
            max_datasets=org.max_datasets,
            max_models=org.max_models,
            max_api_calls_per_month=org.max_api_calls_per_month,
        )
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )


@router.patch("/{org_id}", response_model=OrgResponse)
async def update_organization(
    org_id: str,
    request: UpdateOrgRequest,
    current_user=Depends(get_current_user),
):
    """
    Update organization details.
    
    Only owner or admin can update.
    """
    try:
        org = await orgs_service.get(org_id)
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    # Check if owner or admin
    role = await orgs_service.get_member_role(org_id, current_user.id)
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner or admin access required",
        )
    
    update_data = OrgUpdate(**request.model_dump(exclude_unset=True))
    org = await orgs_service.update(org_id, update_data)
    
    return OrgResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        owner_id=org.owner_id,
        plan=org.plan,
        status=org.status,
        created_at=org.created_at,
        current_members=org.current_members,
        max_members=org.max_members,
    )


@router.delete("/{org_id}", response_model=MessageResponse)
async def delete_organization(
    org_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete organization.
    
    Only owner can delete.
    """
    try:
        org = await orgs_service.get(org_id)
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    if org.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete organization",
        )
    
    await orgs_service.delete(org_id)
    return MessageResponse(message="Organization deleted successfully")


# Member management

@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_members(
    org_id: str,
    current_user=Depends(get_current_user),
):
    """
    List organization members.
    """
    is_member = await orgs_service.is_member(org_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    
    members = await orgs_service.get_members(org_id)
    return [
        MemberResponse(
            id=m.id,
            user_id=m.user_id,
            role=m.role,
            joined_at=m.joined_at,
            invited_by=m.invited_by,
        )
        for m in members
    ]


@router.post("/{org_id}/invite", response_model=MessageResponse)
async def invite_member(
    org_id: str,
    request: InviteMemberRequest,
    current_user=Depends(get_current_user),
):
    """
    Invite a user to the organization.
    
    Only owner or admin can invite.
    """
    role = await orgs_service.get_member_role(org_id, current_user.id)
    if role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner or admin access required",
        )
    
    try:
        await orgs_service.create_invite(
            org_id,
            request.email,
            request.role,
            current_user.id,
        )
        return MessageResponse(message=f"Invite sent to {request.email}")
    except OrgLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{org_id}/members/{user_id}/remove", response_model=MessageResponse)
async def remove_member(
    org_id: str,
    user_id: str,
    current_user=Depends(get_current_user),
):
    """
    Remove a member from the organization.
    
    Owner or admin can remove members. Members can remove themselves.
    """
    role = await orgs_service.get_member_role(org_id, current_user.id)
    
    # Check permissions
    if current_user.id != user_id and role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Prevent owner from leaving
    try:
        org = await orgs_service.get(org_id)
        if org.owner_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner cannot be removed. Transfer ownership first.",
            )
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    
    await orgs_service.remove_member(org_id, user_id)
    return MessageResponse(message="Member removed successfully")


# Quota info

@router.get("/{org_id}/quota")
async def get_quota_info(
    org_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get organization quota information.
    """
    is_member = await orgs_service.is_member(org_id, current_user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    
    try:
        org = await orgs_service.get(org_id)
        return {
            "plan": org.plan.value,
            "quotas": {
                "members": {
                    "current": org.current_members,
                    "max": org.max_members,
                },
                "datasets": {
                    "current": org.current_datasets,
                    "max": org.max_datasets,
                },
                "models": {
                    "current": org.current_models,
                    "max": org.max_models,
                },
                "api_calls": {
                    "current": org.api_calls_this_month,
                    "max": org.max_api_calls_per_month,
                },
                "storage_gb": {
                    "current": org.storage_used_gb,
                    "max": org.storage_limit_gb,
                },
            },
        }
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
