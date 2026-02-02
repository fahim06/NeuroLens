"""
Training Schemas

Request and response models for training endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TrainingStatus(str, Enum):
    """Training job status."""
    
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HyperParameters(BaseModel):
    """Training hyperparameters."""
    
    learning_rate: float = Field(0.001, gt=0, description="Learning rate")
    batch_size: int = Field(32, gt=0, description="Batch size")
    epochs: int = Field(100, gt=0, description="Number of epochs")
    optimizer: str = Field("adam", description="Optimizer name")
    loss: str = Field("categorical_crossentropy", description="Loss function")
    
    # Regularization
    dropout: float = Field(0.5, ge=0, le=1, description="Dropout rate")
    l2_regularization: float = Field(0.0, ge=0, description="L2 regularization factor")
    
    # Early stopping
    early_stopping_patience: int = Field(10, gt=0, description="Early stopping patience")
    early_stopping_min_delta: float = Field(0.001, ge=0, description="Minimum delta for early stopping")
    
    # Data augmentation
    augmentation_enabled: bool = Field(True, description="Enable data augmentation")


class TrainingConfig(BaseModel):
    """Training job configuration."""
    
    dataset_id: str = Field(..., description="Dataset identifier")
    dataset_version: str | None = Field(None, description="Specific dataset version")
    
    model_name: str = Field(..., description="Name for the trained model")
    model_architecture: str = Field("resnet50", description="Base architecture")
    
    hyperparameters: HyperParameters = Field(default_factory=HyperParameters)
    
    # Validation
    validation_split: float = Field(0.2, gt=0, lt=1, description="Validation split ratio")
    cross_validation_folds: int | None = Field(None, description="Number of CV folds")
    
    # Resources
    use_gpu: bool = Field(True, description="Use GPU if available")
    
    # Experiment tracking
    experiment_name: str | None = Field(None, description="MLflow experiment name")
    tags: dict[str, str] = Field(default_factory=dict, description="Job tags")


class TrainingMetrics(BaseModel):
    """Training metrics snapshot."""
    
    epoch: int = Field(..., description="Current epoch")
    train_loss: float = Field(..., description="Training loss")
    train_accuracy: float = Field(..., description="Training accuracy")
    val_loss: float | None = Field(None, description="Validation loss")
    val_accuracy: float | None = Field(None, description="Validation accuracy")
    learning_rate: float = Field(..., description="Current learning rate")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TrainingJobResponse(BaseModel):
    """Training job response."""
    
    job_id: UUID = Field(..., description="Unique job identifier")
    status: TrainingStatus = Field(..., description="Job status")
    config: TrainingConfig = Field(..., description="Job configuration")
    
    # Progress
    current_epoch: int | None = Field(None, description="Current epoch")
    total_epochs: int | None = Field(None, description="Total epochs")
    progress_percent: float | None = Field(None, description="Progress percentage")
    
    # Results
    best_metrics: TrainingMetrics | None = Field(None, description="Best metrics achieved")
    model_id: str | None = Field(None, description="Resulting model ID if completed")
    
    # Metadata
    message: str | None = Field(None, description="Status message")
    error: str | None = Field(None, description="Error message if failed")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(None)
    completed_at: datetime | None = Field(None)
    
    model_config = {"from_attributes": True}
