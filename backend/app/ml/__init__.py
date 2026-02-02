"""
NeuroLens Backend ML Module

Backend-specific ML contracts and preprocessing for API integration.
The core ML architecture lives in the top-level `ml/` package.

This module provides:
- API-level contracts (protocols for type safety)
- Preprocessing utilities for request handling
- Bridge between FastAPI and ML core
"""

from backend.app.ml.contracts import (
    BaseModel as MLBaseModel,
    BaseTrainer,
    BaseExplainer,
    Preprocessor,
    Postprocessor,
)
from backend.app.ml.preprocessing import ImagePreprocessor

__all__ = [
    "MLBaseModel",
    "BaseTrainer",
    "BaseExplainer",
    "Preprocessor",
    "Postprocessor",
    "ImagePreprocessor",
]
