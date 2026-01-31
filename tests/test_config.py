"""
Tests for configuration module.
"""

import os

import pytest

from app.core.config import Settings, get_settings


def test_default_settings() -> None:
    """Test default settings values."""
    settings = Settings()
    assert settings.app_name == "NeuroLens"
    assert settings.app_version == "3.0.0"
    assert settings.api_prefix == "/api/v1"


def test_settings_from_env() -> None:
    """Test settings loaded from environment variables."""
    os.environ["APP_ENV"] = "testing"
    os.environ["APP_DEBUG"] = "true"
    
    settings = Settings()
    assert settings.app_env == "testing"
    assert settings.app_debug is True
    
    # Cleanup
    del os.environ["APP_ENV"]
    del os.environ["APP_DEBUG"]


def test_is_production() -> None:
    """Test production environment detection."""
    settings = Settings(app_env="production")
    assert settings.is_production is True
    assert settings.is_development is False


def test_is_development() -> None:
    """Test development environment detection."""
    settings = Settings(app_env="development")
    assert settings.is_development is True
    assert settings.is_production is False


def test_invalid_log_level() -> None:
    """Test validation of log level."""
    with pytest.raises(ValueError):
        Settings(log_level="INVALID")


def test_cors_origins_parsing() -> None:
    """Test CORS origins parsing from string."""
    settings = Settings(cors_origins='["http://localhost:3000"]')
    assert settings.cors_origins == ["http://localhost:3000"]
