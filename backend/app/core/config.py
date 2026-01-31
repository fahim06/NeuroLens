"""
NeuroLens Configuration Module

Centralized configuration management using Pydantic Settings.
Follows the configuration strategy defined in Phase 1 architecture.

Configuration Sources (priority order):
1. Environment variables
2. .env file
3. Default values
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
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
    # Application Settings
    # =========================================================================
    app_name: str = "NeuroLens"
    app_env: str = "development"
    app_debug: bool = False
    app_version: str = "3.0.0"
    
    # =========================================================================
    # API Settings
    # =========================================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    api_reload: bool = False
    
    # =========================================================================
    # Security Settings
    # =========================================================================
    secret_key: str = "development-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # =========================================================================
    # ML Settings
    # =========================================================================
    ml_model_path: Path = Path("ml/registry")
    ml_dataset_path: Path = Path("ml/datasets")
    ml_cache_path: Path = Path(".cache/ml")
    
    # =========================================================================
    # Logging Settings
    # =========================================================================
    log_level: str = "INFO"
    log_format: str = "json"
    
    # =========================================================================
    # Feature Flags
    # =========================================================================
    feature_training_enabled: bool = True
    feature_explainability_enabled: bool = True
    
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
