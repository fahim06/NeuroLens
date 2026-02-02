"""
Model Schemas

Request and response models for model registry endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    """Model information from registry."""
    
    model_id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    version: str = Field(..., description="Semantic version")
    description: str = Field("", description="Model description")
    architecture: str = Field(..., description="Model architecture type")
    task: str = Field(..., description="Task type (classification, segmentation, etc.)")
    
    # Performance metrics
    metrics: dict[str, float] = Field(default_factory=dict, description="Evaluation metrics")
    
    # Metadata
    input_shape: list[int] = Field(..., description="Expected input shape")
    output_classes: list[str] = Field(default_factory=list, description="Output class labels")
    
    # Status
    is_active: bool = Field(False, description="Whether this version is active")
    is_archived: bool = Field(False, description="Whether model is archived")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Provenance
    training_job_id: str | None = Field(None, description="Training job that produced this model")
    dataset_version: str | None = Field(None, description="Dataset version used for training")
    
    model_config = {"from_attributes": True}


class ModelListResponse(BaseModel):
    """Paginated list of models."""
    
    models: list[ModelInfo] = Field(..., description="List of models")
    total: int = Field(..., description="Total number of models")
    skip: int = Field(..., description="Number of models skipped")
    limit: int = Field(..., description="Maximum models per page")


class ModelVersionInfo(BaseModel):
    """Model version information."""
    
    version: str = Field(..., description="Semantic version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metrics: dict[str, float] = Field(default_factory=dict)
    is_active: bool = Field(False)
    changelog: str = Field("", description="Version changelog")
