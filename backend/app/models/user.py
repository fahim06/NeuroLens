"""
NeuroLens User Model

User and organization data models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles."""
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseModel):
    """User model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: EmailStr
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    status: UserStatus = UserStatus.ACTIVE
    org_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Settings
    email_verified: bool = False
    two_factor_enabled: bool = False
    
    # Quotas
    api_calls_remaining: int = 1000
    storage_used_mb: float = 0.0
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation schema."""
    
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""
    
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    """User response schema (public)."""
    
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole
    status: UserStatus
    org_id: Optional[str] = None
    created_at: datetime
    email_verified: bool
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with database fields."""
    pass
