"""
NeuroLens Users Service

User management service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models.user import User, UserCreate, UserUpdate, UserRole, UserStatus
from app.core.security import hash_password


# In-memory storage (replace with database in production)
_users_db: dict[str, User] = {}


class UserNotFoundError(Exception):
    """User not found error."""
    pass


class UserExistsError(Exception):
    """User already exists error."""
    pass


class UsersService:
    """Users management service."""
    
    @staticmethod
    async def create(user_data: UserCreate, role: UserRole = UserRole.MEMBER) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            role: User role
            
        Returns:
            Created user
        """
        # Check if email exists
        for user in _users_db.values():
            if user.email == user_data.email:
                raise UserExistsError("Email already registered")
            if user.username == user_data.username:
                raise UserExistsError("Username already taken")
        
        user = User(
            id=str(uuid4()),
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=role,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        _users_db[user.id] = user
        return user
    
    @staticmethod
    async def get(user_id: str) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = _users_db.get(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user
    
    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        for user in _users_db.values():
            if user.email == email:
                return user
        return None
    
    @staticmethod
    async def get_by_username(username: str) -> Optional[User]:
        """Get user by username."""
        for user in _users_db.values():
            if user.username == username:
                return user
        return None
    
    @staticmethod
    async def list(
        org_id: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        List users with optional filters.
        
        Args:
            org_id: Filter by organization
            role: Filter by role
            status: Filter by status
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of users
        """
        users = list(_users_db.values())
        
        if org_id:
            users = [u for u in users if u.org_id == org_id]
        if role:
            users = [u for u in users if u.role == role]
        if status:
            users = [u for u in users if u.status == status]
        
        return users[skip:skip + limit]
    
    @staticmethod
    async def update(user_id: str, update_data: UserUpdate) -> User:
        """
        Update user.
        
        Args:
            user_id: User ID
            update_data: Update data
            
        Returns:
            Updated user
        """
        user = _users_db.get(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.now(timezone.utc)
        return user
    
    @staticmethod
    async def delete(user_id: str) -> None:
        """
        Delete user (soft delete by setting status to inactive).
        
        Args:
            user_id: User ID
        """
        user = _users_db.get(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        user.status = UserStatus.INACTIVE
        user.updated_at = datetime.now(timezone.utc)
    
    @staticmethod
    async def hard_delete(user_id: str) -> None:
        """
        Permanently delete user.
        
        Args:
            user_id: User ID
        """
        if user_id in _users_db:
            del _users_db[user_id]
    
    @staticmethod
    async def set_org(user_id: str, org_id: str) -> User:
        """
        Assign user to organization.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            Updated user
        """
        user = _users_db.get(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        
        user.org_id = org_id
        user.updated_at = datetime.now(timezone.utc)
        return user
    
    @staticmethod
    async def count(org_id: Optional[str] = None) -> int:
        """Count users, optionally filtered by organization."""
        if org_id:
            return sum(1 for u in _users_db.values() if u.org_id == org_id)
        return len(_users_db)


# Singleton instance
users_service = UsersService()
