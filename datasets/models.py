import uuid

from django.contrib.auth.models import User
from django.db import models


class Dataset(models.Model):
    """
    Represents a dataset in the system.
    Stores metadata about datasets used for ML training/inference.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    domain = models.CharField(max_length=50, blank=True, default="")
    classes = models.JSONField(default=list, help_text="List of class names")
    version = models.CharField(max_length=20, default="1.0")
    source = models.CharField(max_length=255, blank=True, default="")
    active = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="datasets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"

    def __str__(self):
        return f"{self.name} ({self.owner.username})"
