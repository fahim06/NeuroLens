"""
NeuroLens Hardened Security Module

Security-hardened authentication and authorization utilities.
Implements best practices for JWT, password hashing, and token management.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass

from jose import jwt, JWTError

from app.core.config import settings


# =============================================================================
# Security Configuration
# =============================================================================

class TokenType(str, Enum):
    """Token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


@dataclass
class SecurityConfig:
    """Security configuration with secure defaults."""
    
    # JWT Settings
    jwt_secret_key: str = settings.secret_key
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # Short-lived for security
    refresh_token_expire_days: int = 7
    
    # Password Settings
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    password_hash_iterations: int = 100000
    
    # Rate Limiting
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    # Token Settings
    token_blacklist_enabled: bool = True
    require_token_binding: bool = False  # Bind tokens to IP/User-Agent


SECURITY_CONFIG = SecurityConfig()


# =============================================================================
# Password Hashing (Argon2-like with PBKDF2 fallback)
# =============================================================================

def hash_password_secure(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256 with secure parameters.
    
    Uses high iteration count for resistance against brute-force attacks.
    """
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=SECURITY_CONFIG.password_hash_iterations,
        dklen=32
    )
    # Format: algorithm$iterations$salt$hash
    return f"pbkdf2_sha256${SECURITY_CONFIG.password_hash_iterations}${salt.hex()}${key.hex()}"


def verify_password_secure(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using constant-time comparison.
    """
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        
        algorithm, iterations, salt_hex, hash_hex = parts
        
        if algorithm != "pbkdf2_sha256":
            return False
        
        salt = bytes.fromhex(salt_hex)
        stored_hash = bytes.fromhex(hash_hex)
        
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            iterations=int(iterations),
            dklen=32
        )
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_hash, stored_hash)
    except (ValueError, AttributeError, TypeError):
        return False


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets security requirements.
    
    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []
    
    if len(password) < SECURITY_CONFIG.min_password_length:
        errors.append(f"Password must be at least {SECURITY_CONFIG.min_password_length} characters")
    
    if SECURITY_CONFIG.require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if SECURITY_CONFIG.require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if SECURITY_CONFIG.require_digit and not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if SECURITY_CONFIG.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords
    common_passwords = {'password', 'password123', '123456', 'qwerty', 'letmein'}
    if password.lower() in common_passwords:
        errors.append("Password is too common")
    
    return len(errors) == 0, errors


# =============================================================================
# JWT Token Management (Hardened)
# =============================================================================

class TokenBlacklist:
    """In-memory token blacklist (use Redis in production)."""
    
    _blacklist: set[str] = set()
    _expiry: dict[str, float] = {}
    
    @classmethod
    def add(cls, token_jti: str, expires_at: float) -> None:
        """Add a token to the blacklist."""
        cls._blacklist.add(token_jti)
        cls._expiry[token_jti] = expires_at
        cls._cleanup()
    
    @classmethod
    def is_blacklisted(cls, token_jti: str) -> bool:
        """Check if a token is blacklisted."""
        cls._cleanup()
        return token_jti in cls._blacklist
    
    @classmethod
    def _cleanup(cls) -> None:
        """Remove expired tokens from blacklist."""
        now = time.time()
        expired = [jti for jti, exp in cls._expiry.items() if exp < now]
        for jti in expired:
            cls._blacklist.discard(jti)
            cls._expiry.pop(jti, None)


@dataclass
class TokenPayload:
    """Decoded token payload."""
    sub: str  # Subject (user ID)
    type: TokenType
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    scopes: list[str] = None
    org_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.exp
    
    def is_blacklisted(self) -> bool:
        """Check if token is blacklisted."""
        return TokenBlacklist.is_blacklisted(self.jti)


def create_access_token_secure(
    subject: str,
    scopes: list[str] = None,
    org_id: str = None,
    expires_delta: timedelta = None,
    additional_claims: dict[str, Any] = None,
) -> str:
    """
    Create a secure JWT access token with JTI for revocation.
    
    Args:
        subject: User ID
        scopes: Permission scopes
        org_id: Organization ID
        expires_delta: Custom expiration time
        additional_claims: Additional JWT claims
    
    Returns:
        Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=SECURITY_CONFIG.access_token_expire_minutes))
    
    payload = {
        "sub": subject,
        "type": TokenType.ACCESS.value,
        "exp": expire,
        "iat": now,
        "jti": secrets.token_urlsafe(16),  # Unique token ID
        "scopes": scopes or [],
    }
    
    if org_id:
        payload["org_id"] = org_id
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(
        payload,
        SECURITY_CONFIG.jwt_secret_key,
        algorithm=SECURITY_CONFIG.jwt_algorithm
    )


def create_refresh_token_secure(
    subject: str,
    expires_delta: timedelta = None,
) -> str:
    """
    Create a secure JWT refresh token.
    
    Refresh tokens have longer expiry and can be used to obtain new access tokens.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=SECURITY_CONFIG.refresh_token_expire_days))
    
    payload = {
        "sub": subject,
        "type": TokenType.REFRESH.value,
        "exp": expire,
        "iat": now,
        "jti": secrets.token_urlsafe(16),
    }
    
    return jwt.encode(
        payload,
        SECURITY_CONFIG.jwt_secret_key,
        algorithm=SECURITY_CONFIG.jwt_algorithm
    )


def verify_token_secure(
    token: str,
    expected_type: TokenType = None,
    verify_blacklist: bool = True,
) -> Optional[TokenPayload]:
    """
    Verify and decode a JWT token with security checks.
    
    Args:
        token: JWT token to verify
        expected_type: Expected token type
        verify_blacklist: Whether to check token blacklist
    
    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            SECURITY_CONFIG.jwt_secret_key,
            algorithms=[SECURITY_CONFIG.jwt_algorithm]
        )
        
        # Validate required claims
        required_claims = {"sub", "type", "exp", "iat", "jti"}
        if not required_claims.issubset(payload.keys()):
            return None
        
        # Check token type
        token_type = TokenType(payload["type"])
        if expected_type and token_type != expected_type:
            return None
        
        # Parse payload
        token_payload = TokenPayload(
            sub=payload["sub"],
            type=token_type,
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            jti=payload["jti"],
            scopes=payload.get("scopes", []),
            org_id=payload.get("org_id"),
        )
        
        # Check expiration
        if token_payload.is_expired():
            return None
        
        # Check blacklist
        if verify_blacklist and SECURITY_CONFIG.token_blacklist_enabled:
            if token_payload.is_blacklisted():
                return None
        
        return token_payload
        
    except (JWTError, ValueError, KeyError):
        return None


def revoke_token(token: str) -> bool:
    """
    Revoke a JWT token by adding to blacklist.
    
    Args:
        token: JWT token to revoke
    
    Returns:
        True if revoked, False if invalid
    """
    try:
        payload = jwt.decode(
            token,
            SECURITY_CONFIG.jwt_secret_key,
            algorithms=[SECURITY_CONFIG.jwt_algorithm]
        )
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti and exp:
            TokenBlacklist.add(jti, exp)
            return True
        return False
    except JWTError:
        return False


# =============================================================================
# API Key Management
# =============================================================================

def generate_api_key_secure() -> tuple[str, str]:
    """
    Generate a secure API key with prefix.
    
    Returns:
        Tuple of (full_key, key_hash) - store only the hash
    """
    # Generate a random key
    key_bytes = secrets.token_bytes(32)
    key_id = secrets.token_urlsafe(8)
    key_secret = key_bytes.hex()
    
    # Full key format: nl_<id>_<secret>
    full_key = f"nl_{key_id}_{key_secret}"
    
    # Hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    return full_key, key_hash


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """
    Verify an API key against its stored hash.
    """
    computed_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return hmac.compare_digest(computed_hash, stored_hash)


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate API key format.
    """
    if not api_key or not api_key.startswith("nl_"):
        return False
    
    parts = api_key.split("_")
    if len(parts) != 3:
        return False
    
    # Check key ID and secret lengths
    _, key_id, key_secret = parts
    return len(key_id) == 11 and len(key_secret) == 64


# =============================================================================
# Security Utilities
# =============================================================================

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.
    """
    return hmac.compare_digest(a.encode(), b.encode())


def sanitize_for_log(data: dict[str, Any], sensitive_keys: set[str] = None) -> dict[str, Any]:
    """
    Sanitize data for logging by redacting sensitive fields.
    """
    if sensitive_keys is None:
        sensitive_keys = {
            'password', 'token', 'secret', 'api_key', 'authorization',
            'credit_card', 'ssn', 'private_key', 'access_token', 'refresh_token'
        }
    
    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_log(value, sensitive_keys)
        else:
            sanitized[key] = value
    
    return sanitized


def mask_email(email: str) -> str:
    """Mask email for logging (e.g., j***@example.com)."""
    if not email or '@' not in email:
        return "[INVALID]"
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_ip(ip: str) -> str:
    """Mask IP address for logging (e.g., 192.168.*.*)."""
    if not ip:
        return "[INVALID]"
    
    parts = ip.split('.')
    if len(parts) == 4:  # IPv4
        return f"{parts[0]}.{parts[1]}.*.*"
    return "[MASKED]"
