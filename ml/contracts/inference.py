"""
Inference Contracts — Request/Response Schemas

Defines the contracts for ML inference requests and responses.
Phase 0: Schema definitions only, no validation logic.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


@dataclass
class PredictionResult:
    label: str
    confidence: float
    metadata: dict | None = None


class BasePredictor:
    def predict(self, image) -> PredictionResult:
        raise NotImplementedError


class DetectionType(str, Enum):
    """Supported detection types."""

    HUMAN_ANIMAL = "human_animal"
    ANIMAL_CATEGORY = "animal_category"
    BIOLOGICAL = "biological"
    BRAIN_TUMOR = "brain_tumor"
    CITRUS = "citrus"


@dataclass
class InferenceRequest:
    """
    Request contract for ML inference.

    Phase 0: Basic structure, no validation.
    """

    image_data: Union[str, bytes]  # Base64 string or bytes
    detection_type: Optional[DetectionType] = None
    domain: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization validation (Phase 0: minimal)."""
        if not self.image_data:
            raise ValueError("image_data is required")


@dataclass
class InferenceResponse:
    """
    Response contract for ML inference.

    Phase 0: Basic structure, placeholder values.
    """

    detection_type: DetectionType
    prediction: Union[str, Dict[str, Any]]
    confidence: float
    domain: str
    processing_time_ms: int
    model_version: str
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization validation (Phase 0: minimal)."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class DomainDetectionRequest:
    """
    Request contract for domain detection.

    Phase 0: Basic structure.
    """

    image_data: Union[str, bytes]  # Base64 string or bytes

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.image_data:
            raise ValueError("image_data is required")


@dataclass
class DomainDetectionResponse:
    """
    Response contract for domain detection.

    Phase 0: Basic structure.
    """

    domain: str
    confidence: float
    subcategories: List[str]
    suggested_detection_types: List[DetectionType]

    def __post_init__(self):
        """Post-initialization validation."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
