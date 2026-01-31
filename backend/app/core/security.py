"""
NeuroLens Security Module

Security utilities and configurations.

Rules:
- No hardcoded secrets
- All secrets from environment
- Prepare for JWT auth (Phase 2 stub, implementation in later phases)
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


# =============================================================================
# JWT Configuration (Stub - Full implementation in Phase 9: Security)
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
    
    Stub implementation for Phase 2.
    Full implementation with jose/jwt in Phase 9.
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
    
    Returns:
        str: Encoded JWT token
    """
    # TODO Phase 9: Implement with python-jose
    # from jose import jwt
    # to_encode = data.copy()
    # expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    # to_encode.update({"exp": expire})
    # return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    raise NotImplementedError("JWT authentication not yet implemented. See Phase 9.")


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.
    
    Stub implementation for Phase 2.
    Full implementation in Phase 9.
    
    Args:
        token: JWT token to verify
    
    Returns:
        dict | None: Decoded payload or None if invalid
    """
    # TODO Phase 9: Implement with python-jose
    # from jose import jwt, JWTError
    # try:
    #     payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    #     return payload
    # except JWTError:
    #     return None
    raise NotImplementedError("JWT verification not yet implemented. See Phase 9.")


# =============================================================================
# Password Hashing (Stub - Full implementation in Phase 9)
# =============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Stub implementation for Phase 2.
    
    Args:
        password: Plain text password
    
    Returns:
        str: Hashed password
    """
    # TODO Phase 9: Implement with passlib
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.hash(password)
    raise NotImplementedError("Password hashing not yet implemented. See Phase 9.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Stub implementation for Phase 2.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to compare against
    
    Returns:
        bool: True if password matches
    """
    # TODO Phase 9: Implement with passlib
    # from passlib.context import CryptContext
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # return pwd_context.verify(plain_password, hashed_password)
    raise NotImplementedError("Password verification not yet implemented. See Phase 9.")


# =============================================================================
# API Key Validation (Stub - Full implementation in Phase 9)
# =============================================================================


def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key.
    
    Stub implementation for Phase 2.
    
    Args:
        api_key: API key to validate
    
    Returns:
        bool: True if valid
    """
    # TODO Phase 9: Implement API key validation
    raise NotImplementedError("API key validation not yet implemented. See Phase 9.")
