"""
NeuroLens Security Module

Security utilities for authentication and authorization.
JWT-based auth with password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import hashlib
import secrets

from jose import jwt, JWTError

from app.core.config import settings


# =============================================================================
# Password Hashing (using hashlib for compatibility)
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using SHA256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, stored_hash = hashed_password.split("$")
        password_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return password_hash == stored_hash
    except (ValueError, AttributeError):
        return False


# =============================================================================
# JWT Token Management
# =============================================================================

JWT_SECRET_KEY = settings.secret_key
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRE_MINUTES = settings.jwt_expire_minutes


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
    
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time (default 7 days)
    
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
    
    Returns:
        dict | None: Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode a JWT token without verification (for debugging).
    
    Args:
        token: JWT token to decode
    
    Returns:
        dict: Decoded payload
    
    Raises:
        JWTError: If token is invalid
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


# =============================================================================
# API Key Validation
# =============================================================================


def generate_api_key() -> str:
    """Generate a new API key."""
    import secrets
    return f"nl_{secrets.token_urlsafe(32)}"


def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key format.
    
    Args:
        api_key: API key to validate
    
    Returns:
        bool: True if valid format
    """
    return api_key.startswith("nl_") and len(api_key) > 10
