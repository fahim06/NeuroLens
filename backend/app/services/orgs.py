"""
NeuroLens Organizations Service

Organization and team management service.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from app.models.organization import (
    Organization,
    OrgCreate,
    OrgUpdate,
    OrgMember,
    OrgInvite,
    OrgPlan,
    OrgStatus,
    PLAN_LIMITS,
)


# In-memory storage (replace with database in production)
_orgs_db: dict[str, Organization] = {}
_members_db: dict[str, OrgMember] = {}
_invites_db: dict[str, OrgInvite] = {}


class OrgNotFoundError(Exception):
    """Organization not found error."""
    pass


class OrgExistsError(Exception):
    """Organization already exists error."""
    pass


class OrgLimitError(Exception):
    """Organization limit reached error."""
    pass


class OrgsService:
    """Organizations management service."""
    
    @staticmethod
    async def create(org_data: OrgCreate, owner_id: str) -> Organization:
        """
        Create a new organization.
        
        Args:
            org_data: Organization creation data
            owner_id: Owner user ID
            
        Returns:
            Created organization
        """
        # Check if slug exists
        for org in _orgs_db.values():
            if org.slug == org_data.slug:
                raise OrgExistsError(f"Organization with slug '{org_data.slug}' already exists")
        
        org = Organization(
            id=str(uuid4()),
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
            owner_id=owner_id,
            plan=OrgPlan.FREE,
            status=OrgStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            **PLAN_LIMITS[OrgPlan.FREE],
        )
        
        _orgs_db[org.id] = org
        
        # Add owner as member
        member = OrgMember(
            id=str(uuid4()),
            org_id=org.id,
            user_id=owner_id,
            role="owner",
            joined_at=datetime.now(timezone.utc),
        )
        _members_db[member.id] = member
        
        return org
    
    @staticmethod
    async def get(org_id: str) -> Organization:
        """
        Get organization by ID.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Organization
            
        Raises:
            OrgNotFoundError: If organization not found
        """
        org = _orgs_db.get(org_id)
        if not org:
            raise OrgNotFoundError(f"Organization {org_id} not found")
        return org
    
    @staticmethod
    async def get_by_slug(slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        for org in _orgs_db.values():
            if org.slug == slug:
                return org
        return None
    
    @staticmethod
    async def list(
        owner_id: Optional[str] = None,
        status: Optional[OrgStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Organization]:
        """
        List organizations with optional filters.
        
        Args:
            owner_id: Filter by owner
            status: Filter by status
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of organizations
        """
        orgs = list(_orgs_db.values())
        
        if owner_id:
            orgs = [o for o in orgs if o.owner_id == owner_id]
        if status:
            orgs = [o for o in orgs if o.status == status]
        
        return orgs[skip:skip + limit]
    
    @staticmethod
    async def list_for_user(user_id: str) -> list[Organization]:
        """
        List organizations a user is a member of.
        
        Args:
            user_id: User ID
            
        Returns:
            List of organizations
        """
        org_ids = [m.org_id for m in _members_db.values() if m.user_id == user_id]
        return [_orgs_db[oid] for oid in org_ids if oid in _orgs_db]
    
    @staticmethod
    async def update(org_id: str, update_data: OrgUpdate) -> Organization:
        """
        Update organization.
        
        Args:
            org_id: Organization ID
            update_data: Update data
            
        Returns:
            Updated organization
        """
        org = _orgs_db.get(org_id)
        if not org:
            raise OrgNotFoundError(f"Organization {org_id} not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Handle plan upgrade
        if "plan" in update_dict:
            new_plan = update_dict["plan"]
            limits = PLAN_LIMITS.get(new_plan, {})
            for key, value in limits.items():
                setattr(org, key, value)
        
        for field, value in update_dict.items():
            setattr(org, field, value)
        
        org.updated_at = datetime.now(timezone.utc)
        return org
    
    @staticmethod
    async def delete(org_id: str) -> None:
        """
        Delete organization (soft delete).
        
        Args:
            org_id: Organization ID
        """
        org = _orgs_db.get(org_id)
        if not org:
            raise OrgNotFoundError(f"Organization {org_id} not found")
        
        org.status = OrgStatus.DELETED
        org.updated_at = datetime.now(timezone.utc)
    
    # Member management
    
    @staticmethod
    async def add_member(
        org_id: str,
        user_id: str,
        role: str = "member",
        invited_by: Optional[str] = None,
    ) -> OrgMember:
        """Add a member to organization."""
        org = _orgs_db.get(org_id)
        if not org:
            raise OrgNotFoundError(f"Organization {org_id} not found")
        
        # Check member limit
        if org.max_members != -1 and org.current_members >= org.max_members:
            raise OrgLimitError("Member limit reached")
        
        member = OrgMember(
            id=str(uuid4()),
            org_id=org_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.now(timezone.utc),
            invited_by=invited_by,
        )
        _members_db[member.id] = member
        
        org.current_members += 1
        return member
    
    @staticmethod
    async def remove_member(org_id: str, user_id: str) -> None:
        """Remove a member from organization."""
        member_id = None
        for mid, member in _members_db.items():
            if member.org_id == org_id and member.user_id == user_id:
                member_id = mid
                break
        
        if member_id:
            del _members_db[member_id]
            org = _orgs_db.get(org_id)
            if org:
                org.current_members = max(0, org.current_members - 1)
    
    @staticmethod
    async def get_members(org_id: str) -> list[OrgMember]:
        """Get all members of an organization."""
        return [m for m in _members_db.values() if m.org_id == org_id]
    
    @staticmethod
    async def get_member_role(org_id: str, user_id: str) -> Optional[str]:
        """Get a user's role in an organization."""
        for member in _members_db.values():
            if member.org_id == org_id and member.user_id == user_id:
                return member.role
        return None
    
    @staticmethod
    async def is_member(org_id: str, user_id: str) -> bool:
        """Check if user is a member of organization."""
        return any(
            m.org_id == org_id and m.user_id == user_id
            for m in _members_db.values()
        )
    
    # Invitations
    
    @staticmethod
    async def create_invite(
        org_id: str,
        email: str,
        role: str,
        invited_by: str,
        expires_days: int = 7,
    ) -> OrgInvite:
        """Create an organization invite."""
        invite = OrgInvite(
            id=str(uuid4()),
            org_id=org_id,
            email=email,
            role=role,
            invited_by=invited_by,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days),
        )
        _invites_db[invite.id] = invite
        return invite
    
    @staticmethod
    async def accept_invite(invite_id: str, user_id: str) -> OrgMember:
        """Accept an organization invite."""
        invite = _invites_db.get(invite_id)
        if not invite:
            raise OrgNotFoundError(f"Invite {invite_id} not found")
        
        if invite.expires_at < datetime.now(timezone.utc):
            raise OrgLimitError("Invite has expired")
        
        if invite.accepted:
            raise OrgLimitError("Invite already accepted")
        
        invite.accepted = True
        member = await OrgsService.add_member(
            invite.org_id,
            user_id,
            invite.role,
            invite.invited_by,
        )
        
        return member
    
    # Quota management
    
    @staticmethod
    async def check_quota(org_id: str, resource: str) -> bool:
        """
        Check if organization has quota for a resource.
        
        Args:
            org_id: Organization ID
            resource: Resource type (datasets, models, api_calls)
            
        Returns:
            True if quota available
        """
        org = _orgs_db.get(org_id)
        if not org:
            return False
        
        quota_map = {
            "datasets": (org.current_datasets, org.max_datasets),
            "models": (org.current_models, org.max_models),
            "api_calls": (org.api_calls_this_month, org.max_api_calls_per_month),
            "storage": (org.storage_used_gb, org.storage_limit_gb),
        }
        
        if resource not in quota_map:
            return True
        
        current, limit = quota_map[resource]
        if limit == -1:  # Unlimited
            return True
        
        return current < limit
    
    @staticmethod
    async def increment_usage(org_id: str, resource: str, amount: int = 1) -> None:
        """Increment resource usage for organization."""
        org = _orgs_db.get(org_id)
        if not org:
            return
        
        if resource == "datasets":
            org.current_datasets += amount
        elif resource == "models":
            org.current_models += amount
        elif resource == "api_calls":
            org.api_calls_this_month += amount
        elif resource == "storage":
            org.storage_used_gb += amount


# Singleton instance
orgs_service = OrgsService()
