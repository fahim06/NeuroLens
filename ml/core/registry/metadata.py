"""
Registry Metadata

Defines metadata structures for model registry entries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ModelStatus(str, Enum):
    """Status of a registered model."""
    
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ModelFramework(str, Enum):
    """Supported ML frameworks."""
    
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    SKLEARN = "sklearn"
    CUSTOM = "custom"


@dataclass
class ModelRecord:
    """
    Complete record of a registered model.
    
    Attributes:
        model_id: Unique model identifier
        name: Human-readable model name
        version: Semantic version (e.g., "1.2.3")
        framework: ML framework used
        input_schema: Description of input format
        output_schema: Description of output format
        metrics: Training/evaluation metrics
        dataset_hash: Hash of training dataset
        preprocessor_hash: Hash of preprocessor config
        created_at: Registration timestamp
        updated_at: Last update timestamp
        status: Model lifecycle status
        path: Path to model artifacts
        tags: Searchable tags
        description: Model description
        author: Model author
        extra: Additional metadata
    """
    
    model_id: str
    name: str
    version: str
    framework: ModelFramework
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    metrics: dict[str, float] = field(default_factory=dict)
    dataset_hash: str | None = None
    preprocessor_hash: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: ModelStatus = ModelStatus.DRAFT
    path: Path | None = None
    tags: list[str] = field(default_factory=list)
    description: str = ""
    author: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Full model identifier with version."""
        return f"{self.name}:{self.version}"
    
    @property
    def is_production(self) -> bool:
        """Whether model is in production."""
        return self.status == ModelStatus.PRODUCTION
    
    def promote(self, to_status: ModelStatus) -> None:
        """
        Promote model to new status.
        
        Args:
            to_status: Target status
        """
        self.status = to_status
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "framework": self.framework.value,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "metrics": self.metrics,
            "dataset_hash": self.dataset_hash,
            "preprocessor_hash": self.preprocessor_hash,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "path": str(self.path) if self.path else None,
            "tags": self.tags,
            "description": self.description,
            "author": self.author,
            "extra": self.extra,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelRecord":
        """Create from dictionary."""
        return cls(
            model_id=data["model_id"],
            name=data["name"],
            version=data["version"],
            framework=ModelFramework(data["framework"]),
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            metrics=data.get("metrics", {}),
            dataset_hash=data.get("dataset_hash"),
            preprocessor_hash=data.get("preprocessor_hash"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            status=ModelStatus(data["status"]),
            path=Path(data["path"]) if data.get("path") else None,
            tags=data.get("tags", []),
            description=data.get("description", ""),
            author=data.get("author", ""),
            extra=data.get("extra", {}),
        )


@dataclass
class RegistryMetadata:
    """
    Metadata for the model registry itself.
    
    Attributes:
        name: Registry name
        version: Registry version
        models_count: Number of registered models
        created_at: Registry creation time
        last_updated: Last update time
        storage_backend: Storage backend type
    """
    
    name: str = "neurolens-registry"
    version: str = "1.0.0"
    models_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    storage_backend: str = "local"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "models_count": self.models_count,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "storage_backend": self.storage_backend,
        }
