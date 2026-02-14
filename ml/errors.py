"""
ML-Specific Exceptions

Custom exceptions for the ML system.
Phase 7: Observability & Error Handling.
"""

from typing import Optional


class MLException(Exception):
    """
    Base exception for all ML-related errors.
    """
    pass


class ModelLoadError(MLException):
    """
    Raised when a model fails to load.
    """

    pass


class PredictionError(MLException):
    """
    Raised when prediction fails.
    """

    pass
