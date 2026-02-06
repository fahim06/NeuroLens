"""
ML Models — Metadata Only

This module contains Django models for ML metadata.
NO tensor data or heavy ML objects are stored here.

Phase 0: Metadata models only.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class MLModel(models.Model):
    """
    ML Model metadata.

    Stores information about available models without storing
    the actual model files or weights.
    """

    name = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20)
    domain = models.CharField(max_length=50)
    detection_type = models.CharField(max_length=50)

    # Model specifications
    input_shape = models.JSONField(
        help_text="Expected input shape [height, width, channels]"
    )
    num_classes = models.PositiveIntegerField()
    class_labels = models.JSONField(help_text="List of class labels")

    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["domain", "detection_type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class InferenceLog(models.Model):
    """
    Log of inference requests for monitoring and analytics.

    Phase 0: Basic logging structure.
    """

    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    detection_type = models.CharField(max_length=50)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    # Request metadata
    request_timestamp = models.DateTimeField(auto_now_add=True)
    processing_time_ms = models.PositiveIntegerField(
        help_text="Processing time in milliseconds"
    )

    # Don't store actual images for privacy/security
    image_hash = models.CharField(max_length=64, help_text="SHA256 hash of input image")

    class Meta:
        ordering = ["-request_timestamp"]
        indexes = [
            models.Index(fields=["model", "request_timestamp"]),
            models.Index(fields=["detection_type"]),
        ]

    def __str__(self):
        return f"Inference {self.id} - {self.model.name} ({self.confidence_score:.2f})"
