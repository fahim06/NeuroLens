"""
ML Registry — Model & Dataset Registry

Metadata registry for models and datasets.
Phase 0: Metadata structures only.
"""

from .models import model_registry, DetectionType
from .datasets import dataset_registry

__all__ = [
    "model_registry",
    "dataset_registry",
    "DetectionType",
]
