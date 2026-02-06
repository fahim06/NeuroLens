"""
ML-Specific Exceptions

Custom exceptions for the ML system.
Phase 0: Basic exception hierarchy.
"""

from typing import Optional


class MLBaseException(Exception):
    """
    Base exception for all ML-related errors.

    Phase 0: Basic exception structure.
    """

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ModelNotFoundError(MLBaseException):
    """Raised when a requested model is not found."""

    pass


class ModelLoadError(MLBaseException):
    """Raised when a model fails to load."""

    pass


class PredictionError(MLBaseException):
    """Raised when prediction fails."""

    pass


class DomainDetectionError(MLBaseException):
    """Raised when domain detection fails."""

    pass


class InvalidInputError(MLBaseException):
    """Raised when input data is invalid."""

    pass


class ConfigurationError(MLBaseException):
    """Raised when ML configuration is invalid."""

    pass
