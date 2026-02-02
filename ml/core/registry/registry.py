"""
Model Registry

Central registry for managing model lifecycle, versioning, and retrieval.
"""

import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from ml.core.registry.metadata import (
    ModelFramework,
    ModelRecord,
    ModelStatus,
    RegistryMetadata,
)


class ModelRegistry(ABC):
    """
    Abstract base class for model registries.
    
    Defines the interface for model storage and retrieval.
    """
    
    @abstractmethod
    def register(
        self,
        name: str,
        version: str,
        framework: ModelFramework,
        model_path: Path,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        metrics: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> ModelRecord:
        """
        Register a new model.
        
        Args:
            name: Model name
            version: Model version
            framework: ML framework
            model_path: Path to model artifacts
            input_schema: Input data schema
            output_schema: Output data schema
            metrics: Optional metrics
            **kwargs: Additional metadata
        
        Returns:
            Created ModelRecord
        """
        ...
    
    @abstractmethod
    def get(self, model_id: str) -> ModelRecord | None:
        """
        Get model by ID.
        
        Args:
            model_id: Model identifier
        
        Returns:
            ModelRecord or None if not found
        """
        ...
    
    @abstractmethod
    def get_by_name(
        self,
        name: str,
        version: str | None = None,
    ) -> ModelRecord | None:
        """
        Get model by name and optional version.
        
        Args:
            name: Model name
            version: Optional version, returns latest if None
        
        Returns:
            ModelRecord or None if not found
        """
        ...
    
    @abstractmethod
    def list_models(
        self,
        name: str | None = None,
        status: ModelStatus | None = None,
        tags: list[str] | None = None,
    ) -> list[ModelRecord]:
        """
        List models with optional filters.
        
        Args:
            name: Filter by name
            status: Filter by status
            tags: Filter by tags (any match)
        
        Returns:
            List of matching ModelRecords
        """
        ...
    
    @abstractmethod
    def update_status(
        self,
        model_id: str,
        status: ModelStatus,
    ) -> ModelRecord:
        """
        Update model status.
        
        Args:
            model_id: Model identifier
            status: New status
        
        Returns:
            Updated ModelRecord
        """
        ...
    
    @abstractmethod
    def delete(self, model_id: str) -> bool:
        """
        Delete a model from registry.
        
        Args:
            model_id: Model identifier
        
        Returns:
            True if deleted, False if not found
        """
        ...
    
    @abstractmethod
    def get_production_model(self, name: str) -> ModelRecord | None:
        """
        Get the production version of a model.
        
        Args:
            name: Model name
        
        Returns:
            Production ModelRecord or None
        """
        ...


class LocalModelRegistry(ModelRegistry):
    """
    Local filesystem-based model registry.
    
    Stores model metadata in JSON and artifacts in subdirectories.
    """
    
    REGISTRY_FILE = "registry.json"
    MODELS_DIR = "models"
    
    def __init__(self, base_path: Path) -> None:
        """
        Initialize local registry.
        
        Args:
            base_path: Base directory for registry storage
        """
        self.base_path = Path(base_path)
        self.registry_file = self.base_path / self.REGISTRY_FILE
        self.models_dir = self.base_path / self.MODELS_DIR
        
        # Initialize storage
        self._init_storage()
    
    def _init_storage(self) -> None:
        """Initialize storage directories and files."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.registry_file.exists():
            self._save_registry({
                "metadata": RegistryMetadata().to_dict(),
                "models": {},
            })
    
    def _load_registry(self) -> dict[str, Any]:
        """Load registry data from file."""
        with open(self.registry_file) as f:
            return json.load(f)
    
    def _save_registry(self, data: dict[str, Any]) -> None:
        """Save registry data to file."""
        with open(self.registry_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique model ID."""
        return str(uuid.uuid4())[:8]
    
    def register(
        self,
        name: str,
        version: str,
        framework: ModelFramework,
        model_path: Path,
        input_schema: dict[str, Any],
        output_schema: dict[str, Any],
        metrics: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> ModelRecord:
        """Register a new model."""
        registry = self._load_registry()
        
        # Generate ID
        model_id = self._generate_id()
        
        # Create model directory
        model_dir = self.models_dir / f"{name}_{version}"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Create record
        record = ModelRecord(
            model_id=model_id,
            name=name,
            version=version,
            framework=framework,
            input_schema=input_schema,
            output_schema=output_schema,
            metrics=metrics or {},
            path=model_path,
            **kwargs,
        )
        
        # Store in registry
        registry["models"][model_id] = record.to_dict()
        registry["metadata"]["models_count"] = len(registry["models"])
        registry["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_registry(registry)
        
        return record
    
    def get(self, model_id: str) -> ModelRecord | None:
        """Get model by ID."""
        registry = self._load_registry()
        
        if model_id not in registry["models"]:
            return None
        
        return ModelRecord.from_dict(registry["models"][model_id])
    
    def get_by_name(
        self,
        name: str,
        version: str | None = None,
    ) -> ModelRecord | None:
        """Get model by name and version."""
        registry = self._load_registry()
        
        matching = [
            ModelRecord.from_dict(m)
            for m in registry["models"].values()
            if m["name"] == name
        ]
        
        if not matching:
            return None
        
        if version:
            for record in matching:
                if record.version == version:
                    return record
            return None
        
        # Return latest by created_at
        return max(matching, key=lambda r: r.created_at)
    
    def list_models(
        self,
        name: str | None = None,
        status: ModelStatus | None = None,
        tags: list[str] | None = None,
    ) -> list[ModelRecord]:
        """List models with filters."""
        registry = self._load_registry()
        
        records = [
            ModelRecord.from_dict(m)
            for m in registry["models"].values()
        ]
        
        # Apply filters
        if name:
            records = [r for r in records if r.name == name]
        
        if status:
            records = [r for r in records if r.status == status]
        
        if tags:
            records = [
                r for r in records
                if any(t in r.tags for t in tags)
            ]
        
        return sorted(records, key=lambda r: r.created_at, reverse=True)
    
    def update_status(
        self,
        model_id: str,
        status: ModelStatus,
    ) -> ModelRecord:
        """Update model status."""
        registry = self._load_registry()
        
        if model_id not in registry["models"]:
            raise ValueError(f"Model not found: {model_id}")
        
        record = ModelRecord.from_dict(registry["models"][model_id])
        record.promote(status)
        
        registry["models"][model_id] = record.to_dict()
        self._save_registry(registry)
        
        return record
    
    def delete(self, model_id: str) -> bool:
        """Delete model from registry."""
        registry = self._load_registry()
        
        if model_id not in registry["models"]:
            return False
        
        del registry["models"][model_id]
        registry["metadata"]["models_count"] = len(registry["models"])
        registry["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_registry(registry)
        return True
    
    def get_production_model(self, name: str) -> ModelRecord | None:
        """Get production model by name."""
        models = self.list_models(name=name, status=ModelStatus.PRODUCTION)
        return models[0] if models else None
    
    def compute_hash(self, path: Path) -> str:
        """
        Compute SHA256 hash of a file or directory.
        
        Args:
            path: Path to file or directory
        
        Returns:
            Hex digest of hash
        """
        hasher = hashlib.sha256()
        
        if path.is_file():
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        elif path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    hasher.update(str(file_path.relative_to(path)).encode())
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            hasher.update(chunk)
        
        return hasher.hexdigest()
