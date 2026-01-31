"""
NeuroLens Configuration Module

Phase 2: Backend API Configuration
Centralized configuration management using Pydantic Settings.

Configuration Sources (priority order):
1. Environment variables
2. .env file
3. Default values

Rules:
- Use Pydantic Settings
- Read from environment variables
- Support local, staging, production
- No hardcoded secrets
"""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Phase 2 Required Fields:
    - APP_NAME
    - API_VERSION
    - ENV
    - DEBUG
    - ALLOWED_ORIGINS
    
    All configuration is centralized here following the principle:
    - No secrets in code
    - Environment-based config
    - Explicit over implicit
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # =========================================================================
    # Application Settings (Phase 2 Required)
    # =========================================================================
    app_name: str = "NeuroLens"
    app_env: str = "local"  # local, staging, production
    app_debug: bool = True
    app_version: str = "3.0.0"
    
    # =========================================================================
    # API Settings (Phase 2 Required)
    # =========================================================================
    api_version: str = "v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    api_reload: bool = True
    
    # =========================================================================
    # CORS Settings (Phase 2 Required)
    # =========================================================================
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # =========================================================================
    # Security Settings (Stubs for Phase 9)
    # =========================================================================
    secret_key: str = "development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # =========================================================================
    # Logging Settings
    # =========================================================================
    log_level: str = "INFO"
    log_format: str = "text"  # text in local, json in production
    
    # =========================================================================
    # Validators
    # =========================================================================
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
    
    # =========================================================================
    # Properties
    # =========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.app_env.lower() == "testing"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()
