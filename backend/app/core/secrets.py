"""
NeuroLens Secrets Management Module

Secure secrets handling, environment variable management,
and secrets rotation utilities.
"""
from __future__ import annotations

import os
import re
import base64
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json


class SecretType(str, Enum):
    """Types of secrets."""
    DATABASE_URL = "database_url"
    API_KEY = "api_key"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    WEBHOOK_SECRET = "webhook_secret"
    SERVICE_ACCOUNT = "service_account"


@dataclass
class SecretMetadata:
    """Metadata for a managed secret."""
    name: str
    secret_type: SecretType
    created_at: datetime
    rotated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    version: int = 1
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if secret is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def needs_rotation(self, max_age_days: int = 90) -> bool:
        """Check if secret needs rotation based on age."""
        reference_time = self.rotated_at or self.created_at
        age = datetime.now(timezone.utc) - reference_time
        return age.days > max_age_days


class SecretsManager:
    """
    Secure secrets management.
    
    In production, integrate with:
    - AWS Secrets Manager
    - HashiCorp Vault
    - Azure Key Vault
    - GCP Secret Manager
    """
    
    def __init__(self):
        self._secrets: dict[str, str] = {}
        self._metadata: dict[str, SecretMetadata] = {}
        self._load_from_environment()
    
    def _load_from_environment(self) -> None:
        """Load secrets from environment variables."""
        secret_patterns = {
            "DATABASE_URL": SecretType.DATABASE_URL,
            "SECRET_KEY": SecretType.JWT_SECRET,
            "JWT_SECRET": SecretType.JWT_SECRET,
            "ENCRYPTION_KEY": SecretType.ENCRYPTION_KEY,
            "API_KEY": SecretType.API_KEY,
        }
        
        for env_var, secret_type in secret_patterns.items():
            value = os.getenv(env_var)
            if value:
                self._secrets[env_var] = value
                self._metadata[env_var] = SecretMetadata(
                    name=env_var,
                    secret_type=secret_type,
                    created_at=datetime.now(timezone.utc),
                    description=f"Loaded from environment variable {env_var}",
                )
    
    def get(self, name: str) -> Optional[str]:
        """
        Get a secret value.
        
        Args:
            name: Secret name
        
        Returns:
            Secret value or None
        """
        return self._secrets.get(name)
    
    def set(
        self,
        name: str,
        value: str,
        secret_type: SecretType,
        expires_at: datetime = None,
        description: str = "",
    ) -> None:
        """
        Set a secret value.
        
        Args:
            name: Secret name
            value: Secret value
            secret_type: Type of secret
            expires_at: Optional expiration time
            description: Optional description
        """
        now = datetime.now(timezone.utc)
        
        if name in self._metadata:
            # Rotating existing secret
            metadata = self._metadata[name]
            metadata.rotated_at = now
            metadata.version += 1
            metadata.expires_at = expires_at
        else:
            # New secret
            metadata = SecretMetadata(
                name=name,
                secret_type=secret_type,
                created_at=now,
                expires_at=expires_at,
                description=description,
            )
        
        self._secrets[name] = value
        self._metadata[name] = metadata
    
    def delete(self, name: str) -> bool:
        """Delete a secret."""
        if name in self._secrets:
            del self._secrets[name]
            self._metadata.pop(name, None)
            return True
        return False
    
    def list_secrets(self) -> list[SecretMetadata]:
        """List all secret metadata (not values)."""
        return list(self._metadata.values())
    
    def get_secrets_needing_rotation(self, max_age_days: int = 90) -> list[str]:
        """Get list of secrets that need rotation."""
        return [
            name for name, metadata in self._metadata.items()
            if metadata.needs_rotation(max_age_days)
        ]
    
    def get_expired_secrets(self) -> list[str]:
        """Get list of expired secrets."""
        return [
            name for name, metadata in self._metadata.items()
            if metadata.is_expired()
        ]


# Global secrets manager
secrets_manager = SecretsManager()


# =============================================================================
# Secret Generation Utilities
# =============================================================================

def generate_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(length)


def generate_encryption_key() -> bytes:
    """Generate a 256-bit encryption key."""
    return secrets.token_bytes(32)


def generate_api_key() -> str:
    """Generate an API key with prefix."""
    return f"nl_{secrets.token_urlsafe(32)}"


def generate_webhook_secret() -> str:
    """Generate a webhook signing secret."""
    return f"whsec_{secrets.token_urlsafe(24)}"


# =============================================================================
# Environment Variable Validation
# =============================================================================

class EnvironmentValidator:
    """Validate required environment variables."""
    
    REQUIRED_VARS = [
        "SECRET_KEY",
        "DATABASE_URL",
    ]
    
    OPTIONAL_VARS = [
        "SENTRY_DSN",
        "REDIS_URL",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ]
    
    # Patterns to validate specific variable types
    VALIDATION_PATTERNS = {
        "DATABASE_URL": r"^(postgresql|mysql|sqlite)://",
        "REDIS_URL": r"^redis://",
        "SECRET_KEY": r"^.{32,}$",  # At least 32 characters
    }
    
    @classmethod
    def validate_all(cls) -> tuple[bool, list[str]]:
        """
        Validate all required environment variables.
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required environment variable: {var}")
            elif var in cls.VALIDATION_PATTERNS:
                if not re.match(cls.VALIDATION_PATTERNS[var], value):
                    errors.append(f"Invalid format for {var}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def check_for_secrets_in_code(cls, code: str) -> list[str]:
        """
        Check code for hardcoded secrets.
        
        Returns:
            List of potential secret leaks
        """
        patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token"),
            (r'-----BEGIN.*PRIVATE KEY-----', "Private key in code"),
        ]
        
        findings = []
        for pattern, description in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append(description)
        
        return findings


# =============================================================================
# Secrets Scanning for CI/CD
# =============================================================================

class SecretsScanner:
    """
    Scan files and content for leaked secrets.
    """
    
    # Common secret patterns
    SECRET_PATTERNS = [
        # API Keys
        (r'(sk_live_[a-zA-Z0-9]{24,})', 'Stripe Live Secret Key'),
        (r'(sk_test_[a-zA-Z0-9]{24,})', 'Stripe Test Secret Key'),
        (r'(ghp_[a-zA-Z0-9]{36})', 'GitHub Personal Access Token'),
        (r'(gho_[a-zA-Z0-9]{36})', 'GitHub OAuth Token'),
        (r'(ghu_[a-zA-Z0-9]{36})', 'GitHub User Token'),
        (r'(ghs_[a-zA-Z0-9]{36})', 'GitHub Server Token'),
        (r'(ghr_[a-zA-Z0-9]{36})', 'GitHub Refresh Token'),
        
        # AWS
        (r'(AKIA[0-9A-Z]{16})', 'AWS Access Key ID'),
        (r'([0-9a-zA-Z/+]{40})', 'Potential AWS Secret Key'),
        
        # Generic
        (r'(api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9-_]{20,})', 'Generic API Key'),
        (r'(secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9-_]{20,})', 'Generic Secret'),
        (r'(password["\']?\s*[:=]\s*["\']?[^"\'\s]{8,})', 'Hardcoded Password'),
        
        # JWT
        (r'(eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})', 'JWT Token'),
        
        # Private Keys
        (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----', 'Private Key'),
    ]
    
    # Files to skip
    SKIP_PATTERNS = [
        r'\.git/',
        r'node_modules/',
        r'__pycache__/',
        r'\.pyc$',
        r'\.env\.example$',
        r'\.env\.sample$',
    ]
    
    @classmethod
    def scan_content(cls, content: str) -> list[dict[str, Any]]:
        """
        Scan content for potential secrets.
        
        Returns:
            List of findings with pattern and match info
        """
        findings = []
        
        for pattern, description in cls.SECRET_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                findings.append({
                    "type": description,
                    "pattern": pattern,
                    "match": match.group(0)[:20] + "...",  # Truncate for safety
                    "position": match.start(),
                })
        
        return findings
    
    @classmethod
    def should_skip_file(cls, filepath: str) -> bool:
        """Check if file should be skipped during scanning."""
        for pattern in cls.SKIP_PATTERNS:
            if re.search(pattern, filepath):
                return True
        return False


# =============================================================================
# Secure Configuration Loading
# =============================================================================

def load_secure_config(config_path: str = None) -> dict[str, Any]:
    """
    Load configuration securely with secret substitution.
    
    Supports ${ENV_VAR} syntax for secret injection.
    """
    config = {}
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Substitute environment variables
    def substitute_env_vars(obj: Any) -> Any:
        if isinstance(obj, str):
            # Replace ${VAR} patterns
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)
            for match in matches:
                env_value = os.getenv(match, '')
                obj = obj.replace(f'${{{match}}}', env_value)
            return obj
        elif isinstance(obj, dict):
            return {k: substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [substitute_env_vars(item) for item in obj]
        return obj
    
    return substitute_env_vars(config)
