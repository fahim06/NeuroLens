import uuid
from django.db import models
from django.contrib.auth.models import User
from datasets.models import Dataset


class InferenceRequest(models.Model):
    """
    Represents an inference/prediction request.
    Tracks the status and results of ML predictions.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='inference_requests'
    )
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inference_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    input_data = models.JSONField(default=dict, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inference Request'
        verbose_name_plural = 'Inference Requests'
    
    def __str__(self):
        return f"Inference {self.id} ({self.status})"
