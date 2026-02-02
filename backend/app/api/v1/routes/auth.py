"""
NeuroLens Authentication API Routes

Endpoints for authentication, registration, and token management.
"""

from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr, Field

from app.services.auth import auth_service, AuthenticationError
from app.models.user import UserCreate, UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Schemas

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Routes

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    
    Creates a new user with the provided credentials.
    Returns the created user (without sensitive fields).
    """
    try:
        user_data = UserCreate(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name,
        )
        user = await auth_service.register(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email and password.
    
    Returns access and refresh tokens on success.
    """
    try:
        access_token, refresh_token, _ = await auth_service.authenticate(
            request.email,
            request.password,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    
    Returns new access and refresh tokens.
    """
    try:
        access_token, refresh_token = await auth_service.refresh_tokens(request.refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    authorization: str = Header(..., description="Bearer token"),
    refresh_token: Optional[str] = None,
):
    """
    Logout and invalidate tokens.
    
    Blacklists the access token and optionally the refresh token.
    """
    token = authorization.replace("Bearer ", "")
    await auth_service.logout(token, refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header(..., description="Bearer token")):
    """
    Get current authenticated user.
    
    Returns the user associated with the provided token.
    """
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
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
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    authorization: str = Header(..., description="Bearer token"),
):
    """
    Change user password.
    
    Requires current password for verification.
    """
    try:
        token = authorization.replace("Bearer ", "")
        user = await auth_service.get_current_user(token)
        await auth_service.change_password(
            user.id,
            request.current_password,
            request.new_password,
        )
        return MessageResponse(message="Password changed successfully")
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/verify-email/{user_id}", response_model=MessageResponse)
async def verify_email(user_id: str):
    """
    Verify user email.
    
    In production, this would be triggered by an email link.
    """
    await auth_service.verify_email(user_id)
    return MessageResponse(message="Email verified successfully")
