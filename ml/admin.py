"""
ML Admin Configuration

Django admin interface for ML models and monitoring.
"""

from django.contrib import admin
from .models import MLModel, InferenceLog


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    """Admin interface for ML models."""

    list_display = [
        "name",
        "version",
        "domain",
        "detection_type",
        "is_active",
        "created_at",
    ]
    list_filter = ["domain", "detection_type", "is_active", "created_at"]
    search_fields = ["name", "domain", "detection_type"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "version", "domain", "detection_type", "description")},
        ),
        (
            "Model Specifications",
            {"fields": ("input_shape", "num_classes", "class_labels")},
        ),
        ("Status", {"fields": ("is_active", "created_at", "updated_at")}),
    )


@admin.register(InferenceLog)
class InferenceLogAdmin(admin.ModelAdmin):
    """Admin interface for inference logs."""

    list_display = [
        "id",
        "model",
        "detection_type",
        "confidence_score",
        "request_timestamp",
        "processing_time_ms",
    ]
    list_filter = ["detection_type", "model", "request_timestamp"]
    search_fields = ["model__name", "detection_type"]
    readonly_fields = ["request_timestamp"]

    fieldsets = (
        (
            "Inference Details",
            {
                "fields": (
                    "model",
                    "detection_type",
                    "confidence_score",
                    "processing_time_ms",
                )
            },
        ),
        ("Request Information", {"fields": ("image_hash", "request_timestamp")}),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of inference logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of inference logs."""
        return False
