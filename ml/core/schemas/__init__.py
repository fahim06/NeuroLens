"""
ML Schemas Module

Defines input/output schemas and data validation for the ML pipeline.
"""

from ml.core.schemas.input import ImageInput, ImageBatch, DatasetInfo
from ml.core.schemas.output import (
    PredictionOutput,
    ClassificationResult,
    BatchPredictionResult,
)
from ml.core.schemas.metrics import (
    MetricValue,
    MetricsReport,
    ClassificationMetrics,
    TrainingMetrics,
)

__all__ = [
    # Input schemas
    "ImageInput",
    "ImageBatch",
    "DatasetInfo",
    # Output schemas
    "PredictionOutput",
    "ClassificationResult",
    "BatchPredictionResult",
    # Metrics schemas
    "MetricValue",
    "MetricsReport",
    "ClassificationMetrics",
    "TrainingMetrics",
]
