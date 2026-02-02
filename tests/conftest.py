"""
Test fixtures and configuration for pytest.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings


@pytest.fixture
def client() -> TestClient:
    """Create test client for API testing."""
    return TestClient(app)


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings instance."""
    return Settings(
        app_env="testing",
        app_debug=True,
        secret_key="test-secret-key",
    )
