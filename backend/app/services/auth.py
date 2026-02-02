"""
NeuroLens Authentication Service

Handles user authentication, token management, and session handling.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User, UserCreate, UserStatus, UserRole


# In-memory storage (replace with database in production)
_users_db: dict[str, User] = {}
_tokens_blacklist: set[str] = set()


class AuthenticationError(Exception):
    """Authentication error."""
    pass


class AuthService:
    """Authentication service."""
    
    @staticmethod
    async def register(user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user
            
        Raises:
            AuthenticationError: If email already exists
        """
        # Check if email exists
        for user in _users_db.values():
            if user.email == user_data.email:
                raise AuthenticationError("Email already registered")
            if user.username == user_data.username:
                raise AuthenticationError("Username already taken")
        
        # Create user
        user = User(
            id=str(uuid4()),
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=UserRole.MEMBER,
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        _users_db[user.id] = user
        return user
    
    @staticmethod
    async def authenticate(email: str, password: str) -> tuple[str, str, User]:
        """
        Authenticate a user and return tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        user = None
        for u in _users_db.values():
            if u.email == email:
                user = u
                break
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(f"Account is {user.status.value}")
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        # Generate tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return access_token, refresh_token, user
    
    @staticmethod
    async def refresh_tokens(refresh_token: str) -> tuple[str, str]:
        """
        Refresh access and refresh tokens.
        
        Args:
            refresh_token: Current refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            AuthenticationError: If token is invalid
        """
        if refresh_token in _tokens_blacklist:
            raise AuthenticationError("Token has been revoked")
        
        payload = verify_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        user_id = payload.get("sub")
        user = _users_db.get(user_id)
        
        if not user or user.status != UserStatus.ACTIVE:
            raise AuthenticationError("User not found or inactive")
        
        # Blacklist old refresh token
        _tokens_blacklist.add(refresh_token)
        
        # Generate new tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
        }
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return new_access_token, new_refresh_token
    
    @staticmethod
    async def logout(access_token: str, refresh_token: Optional[str] = None) -> None:
        """
        Logout user by blacklisting tokens.
        
        Args:
            access_token: Current access token
            refresh_token: Optional refresh token to revoke
        """
        _tokens_blacklist.add(access_token)
        if refresh_token:
            _tokens_blacklist.add(refresh_token)
    
    @staticmethod
    async def get_current_user(token: str) -> User:
        """
        Get current user from token.
        
        Args:
            token: Access token
            
        Returns:
            Current user
            
        Raises:
            AuthenticationError: If token is invalid
        """
        if token in _tokens_blacklist:
            raise AuthenticationError("Token has been revoked")
        
        payload = verify_token(token)
        if not payload:
            raise AuthenticationError("Invalid token")
        
        user_id = payload.get("sub")
        user = _users_db.get(user_id)
        
        if not user:
            raise AuthenticationError("User not found")
        
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(f"Account is {user.status.value}")
        
        return user
    
    @staticmethod
    async def change_password(
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Raises:
            AuthenticationError: If current password is incorrect
        """
        user = _users_db.get(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
    
    @staticmethod
    async def verify_email(user_id: str) -> None:
        """Mark user email as verified."""
        user = _users_db.get(user_id)
        if user:
            user.email_verified = True
            user.updated_at = datetime.now(timezone.utc)
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if token is blacklisted."""
        return token in _tokens_blacklist


# Singleton instance
auth_service = AuthService()
