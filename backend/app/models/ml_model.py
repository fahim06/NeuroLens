"""
NeuroLens Model Registry Model

ML model metadata models for the product layer.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ModelStatus(str, Enum):
    """Model status."""
    DRAFT = "draft"
    TRAINING = "training"
    VALIDATING = "validating"
    STAGED = "staged"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelType(str, Enum):
    """Model type."""
    CLASSIFICATION = "classification"
    SEGMENTATION = "segmentation"
    DETECTION = "detection"
    OTHER = "other"


class MLModel(BaseModel):
    """ML Model registry entry."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Ownership
    org_id: str
    created_by: str
    
    # Type & Status
    model_type: ModelType = ModelType.CLASSIFICATION
    status: ModelStatus = ModelStatus.DRAFT
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Architecture
    framework: str = "tensorflow"
    architecture: Optional[str] = None
    input_shape: Optional[list[int]] = None
    output_classes: int = 0
    class_names: list[str] = Field(default_factory=list)
    
    # Training
    training_dataset_id: Optional[str] = None
    training_run_id: Optional[str] = None
    training_config: dict[str, Any] = Field(default_factory=dict)
    
    # Metrics
    metrics: dict[str, float] = Field(default_factory=dict)
    validation_metrics: dict[str, float] = Field(default_factory=dict)
    
    # Artifacts
    artifact_path: Optional[str] = None
    model_hash: Optional[str] = None
    size_mb: float = 0.0
    
    # Inference
    inference_latency_ms: Optional[float] = None
    batch_inference_supported: bool = True
    
    # Tags
    tags: list[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    """Model creation schema."""
    
    name: str
    description: Optional[str] = None
    model_type: ModelType = ModelType.CLASSIFICATION
    framework: str = "tensorflow"
    tags: list[str] = Field(default_factory=list)


class ModelUpdate(BaseModel):
    """Model update schema."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ModelStatus] = None
    tags: Optional[list[str]] = None


class ModelResponse(BaseModel):
    """Model response schema."""
    
    id: str
    name: str
    description: Optional[str] = None
    version: str
    org_id: str
    created_by: str
    model_type: ModelType
    status: ModelStatus
    framework: str
    created_at: datetime
    updated_at: datetime
    metrics: dict[str, float]
    output_classes: int
    class_names: list[str]
    tags: list[str]
    
    class Config:
        from_attributes = True


class ModelVersion(BaseModel):
    """Model version entry."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    model_id: str
    version: str
    model_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    metrics: dict[str, float] = Field(default_factory=dict)
    changelog: Optional[str] = None
    parent_version_id: Optional[str] = None
    status: ModelStatus = ModelStatus.STAGED
