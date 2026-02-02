"""
NeuroLens Organization Model

Organization and team data models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class OrgPlan(str, Enum):
    """Organization plan tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class OrgStatus(str, Enum):
    """Organization status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Organization(BaseModel):
    """Organization model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    slug: str
    description: Optional[str] = None
    
    # Owner
    owner_id: str
    
    # Plan & Status
    plan: OrgPlan = OrgPlan.FREE
    status: OrgStatus = OrgStatus.ACTIVE
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Quotas
    max_members: int = 5
    max_datasets: int = 10
    max_models: int = 5
    max_api_calls_per_month: int = 10000
    storage_limit_gb: float = 10.0
    
    # Usage
    current_members: int = 1
    current_datasets: int = 0
    current_models: int = 0
    api_calls_this_month: int = 0
    storage_used_gb: float = 0.0
    
    class Config:
        from_attributes = True


class OrgCreate(BaseModel):
    """Organization creation schema."""
    
    name: str
    slug: str
    description: Optional[str] = None


class OrgUpdate(BaseModel):
    """Organization update schema."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    plan: Optional[OrgPlan] = None


class OrgResponse(BaseModel):
    """Organization response schema."""
    
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    owner_id: str
    plan: OrgPlan
    status: OrgStatus
    created_at: datetime
    current_members: int
    current_datasets: int
    current_models: int
    
    class Config:
        from_attributes = True


class OrgMember(BaseModel):
    """Organization member model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    org_id: str
    user_id: str
    role: str = "member"  # owner, admin, member, viewer
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    invited_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrgInvite(BaseModel):
    """Organization invite model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    org_id: str
    email: str
    role: str = "member"
    invited_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    accepted: bool = False


# Plan limits
PLAN_LIMITS = {
    OrgPlan.FREE: {
        "max_members": 5,
        "max_datasets": 10,
        "max_models": 5,
        "max_api_calls_per_month": 10000,
        "storage_limit_gb": 10.0,
    },
    OrgPlan.PRO: {
        "max_members": 25,
        "max_datasets": 100,
        "max_models": 25,
        "max_api_calls_per_month": 100000,
        "storage_limit_gb": 100.0,
    },
    OrgPlan.ENTERPRISE: {
        "max_members": -1,  # Unlimited
        "max_datasets": -1,
        "max_models": -1,
        "max_api_calls_per_month": -1,
        "storage_limit_gb": -1,
    },
}
