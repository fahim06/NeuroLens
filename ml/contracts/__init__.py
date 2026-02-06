"""
ML Contracts — Interfaces & Schemas

This module defines the contracts (interfaces and schemas) for the ML system.
Phase 0: Interfaces only, no implementations.
"""

# Import key contracts for easy access
from .domain import PrimaryDomain, SubCategory
from .inference import InferenceRequest, InferenceResponse

__all__ = [
    "PrimaryDomain",
    "SubCategory",
    "InferenceRequest",
    "InferenceResponse",
]
