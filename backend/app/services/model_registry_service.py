"""
Model Registry Service

Handles model versioning and management.

Responsibilities:
- Model storage
- Version management
- Metadata tracking
- Model activation
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.schemas.models import ModelInfo, ModelVersionInfo


class ModelRegistryService:
    """
    Service for managing model registry.
    
    Versioning Strategy (per Phase 1):
    - Models: semantic versioning
    - Schema versioning for features
    """
    
    def __init__(self, registry_path: Path | None = None) -> None:
        """
        Initialize model registry service.
        
        Args:
            registry_path: Path to model registry
        """
        self.registry_path = registry_path or settings.ml_model_path
        self._models: dict[str, ModelInfo] = {}
    
    async def list_models(
        self,
        skip: int = 0,
        limit: int = 100,
        include_archived: bool = False,
    ) -> tuple[list[ModelInfo], int]:
        """
        List all models in registry.
        
        Args:
            skip: Pagination offset
            limit: Max results
            include_archived: Include archived models
        
        Returns:
            Tuple of (models, total_count)
        """
        models = list(self._models.values())
        
        if not include_archived:
            models = [m for m in models if not m.is_archived]
        
        total = len(models)
        models = models[skip:skip + limit]
        
        return models, total
    
    async def get_model(self, model_id: str) -> ModelInfo | None:
        """
        Get model by ID.
        
        Args:
            model_id: Model identifier
        
        Returns:
            Model info or None
        """
        return self._models.get(model_id)
    
    async def register_model(
        self,
        model_id: str,
        name: str,
        version: str,
        architecture: str,
        task: str,
        input_shape: list[int],
        metrics: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> ModelInfo:
        """
        Register a new model version.
        
        Args:
            model_id: Unique identifier
            name: Human-readable name
            version: Semantic version
            architecture: Model architecture
            task: Task type
            input_shape: Expected input shape
            metrics: Evaluation metrics
        
        Returns:
            Registered model info
        """
        model = ModelInfo(
            model_id=model_id,
            name=name,
            version=version,
            architecture=architecture,
            task=task,
            input_shape=input_shape,
            metrics=metrics or {},
            **kwargs,
        )
        
        self._models[model_id] = model
        return model
    
    async def activate_version(self, model_id: str, version: str) -> bool:
        """
        Activate a specific model version.
        
        Args:
            model_id: Model identifier
            version: Version to activate
        
        Returns:
            True if activated
        """
        model = self._models.get(model_id)
        if not model:
            return False
        
        # Deactivate other versions of same model base
        # TODO: Implement multi-version management
        
        model.is_active = True
        model.updated_at = datetime.utcnow()
        
        return True
    
    async def archive_model(self, model_id: str) -> bool:
        """
        Archive a model.
        
        Args:
            model_id: Model identifier
        
        Returns:
            True if archived
        """
        model = self._models.get(model_id)
        if not model:
            return False
        
        model.is_archived = True
        model.is_active = False
        model.updated_at = datetime.utcnow()
        
        return True


# Service singleton
_registry_service: ModelRegistryService | None = None


def get_model_registry_service() -> ModelRegistryService:
    """Get or create model registry service instance."""
    global _registry_service
    if _registry_service is None:
        _registry_service = ModelRegistryService()
    return _registry_service
