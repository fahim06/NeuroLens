"""
NeuroLens Dataset Model

Dataset metadata models for the product layer.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DatasetStatus(str, Enum):
    """Dataset status."""
    DRAFT = "draft"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    ARCHIVED = "archived"


class DatasetType(str, Enum):
    """Dataset type."""
    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"
    PRODUCTION = "production"


class Dataset(BaseModel):
    """Dataset model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Ownership
    org_id: str
    created_by: str
    
    # Type & Status
    dataset_type: DatasetType = DatasetType.TRAINING
    status: DatasetStatus = DatasetStatus.DRAFT
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Statistics
    num_samples: int = 0
    num_classes: int = 0
    class_names: list[str] = Field(default_factory=list)
    class_distribution: dict[str, int] = Field(default_factory=dict)
    
    # Storage
    storage_path: Optional[str] = None
    size_mb: float = 0.0
    file_count: int = 0
    
    # Hashing
    data_hash: Optional[str] = None
    manifest_hash: Optional[str] = None
    
    # Validation
    validation_report_id: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    
    # Tags
    tags: list[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    """Dataset creation schema."""
    
    name: str
    description: Optional[str] = None
    dataset_type: DatasetType = DatasetType.TRAINING
    tags: list[str] = Field(default_factory=list)


class DatasetUpdate(BaseModel):
    """Dataset update schema."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_type: Optional[DatasetType] = None
    status: Optional[DatasetStatus] = None
    tags: Optional[list[str]] = None


class DatasetResponse(BaseModel):
    """Dataset response schema."""
    
    id: str
    name: str
    description: Optional[str] = None
    version: str
    org_id: str
    created_by: str
    dataset_type: DatasetType
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime
    num_samples: int
    num_classes: int
    class_names: list[str]
    size_mb: float
    tags: list[str]
    
    class Config:
        from_attributes = True


class DatasetVersion(BaseModel):
    """Dataset version model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    dataset_id: str
    version: str
    data_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    changelog: Optional[str] = None
    parent_version_id: Optional[str] = None
