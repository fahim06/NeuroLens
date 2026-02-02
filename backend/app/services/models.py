"""
NeuroLens Models Service

ML model registry management service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models.ml_model import (
    MLModel,
    ModelCreate,
    ModelUpdate,
    ModelVersion,
    ModelStatus,
    ModelType,
)


# In-memory storage (replace with database in production)
_models_db: dict[str, MLModel] = {}
_versions_db: dict[str, ModelVersion] = {}


class ModelNotFoundError(Exception):
    """Model not found error."""
    pass


class ModelsService:
    """ML models registry management service."""
    
    @staticmethod
    async def create(
        model_data: ModelCreate,
        org_id: str,
        user_id: str,
    ) -> MLModel:
        """
        Create a new model entry.
        
        Args:
            model_data: Model creation data
            org_id: Organization ID
            user_id: Creator user ID
            
        Returns:
            Created model
        """
        model = MLModel(
            id=str(uuid4()),
            name=model_data.name,
            description=model_data.description,
            org_id=org_id,
            created_by=user_id,
            model_type=model_data.model_type,
            framework=model_data.framework,
            status=ModelStatus.DRAFT,
            tags=model_data.tags,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        _models_db[model.id] = model
        return model
    
    @staticmethod
    async def get(model_id: str) -> MLModel:
        """
        Get model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Model
            
        Raises:
            ModelNotFoundError: If model not found
        """
        model = _models_db.get(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        return model
    
    @staticmethod
    async def list(
        org_id: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        tags: Optional[list[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[MLModel]:
        """
        List models with optional filters.
        
        Args:
            org_id: Filter by organization
            model_type: Filter by type
            status: Filter by status
            tags: Filter by tags (any match)
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of models
        """
        models = list(_models_db.values())
        
        if org_id:
            models = [m for m in models if m.org_id == org_id]
        if model_type:
            models = [m for m in models if m.model_type == model_type]
        if status:
            models = [m for m in models if m.status == status]
        if tags:
            models = [m for m in models if any(t in m.tags for t in tags)]
        
        return models[skip:skip + limit]
    
    @staticmethod
    async def get_production_model(org_id: str) -> Optional[MLModel]:
        """Get the production model for an organization."""
        for model in _models_db.values():
            if model.org_id == org_id and model.status == ModelStatus.PRODUCTION:
                return model
        return None
    
    @staticmethod
    async def update(model_id: str, update_data: ModelUpdate) -> MLModel:
        """
        Update model.
        
        Args:
            model_id: Model ID
            update_data: Update data
            
        Returns:
            Updated model
        """
        model = _models_db.get(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(model, field, value)
        
        model.updated_at = datetime.now(timezone.utc)
        return model
    
    @staticmethod
    async def delete(model_id: str) -> None:
        """
        Delete model (soft delete by archiving).
        
        Args:
            model_id: Model ID
        """
        model = _models_db.get(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        model.status = ModelStatus.ARCHIVED
        model.updated_at = datetime.now(timezone.utc)
    
    @staticmethod
    async def set_status(model_id: str, status: ModelStatus) -> MLModel:
        """Update model status."""
        model = _models_db.get(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        # If promoting to production, demote current production model
        if status == ModelStatus.PRODUCTION:
            for m in _models_db.values():
                if m.org_id == model.org_id and m.status == ModelStatus.PRODUCTION:
                    m.status = ModelStatus.STAGED
                    m.updated_at = datetime.now(timezone.utc)
        
        model.status = status
        model.updated_at = datetime.now(timezone.utc)
        return model
    
    @staticmethod
    async def update_metrics(
        model_id: str,
        metrics: dict[str, float],
    ) -> MLModel:
        """Update model metrics."""
        model = _models_db.get(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        model.metrics.update(metrics)
        model.updated_at = datetime.now(timezone.utc)
        return model
    
    # Version management
    
    @staticmethod
    async def create_version(
        model_id: str,
        version: str,
        model_hash: str,
        user_id: str,
        metrics: Optional[dict[str, float]] = None,
        changelog: Optional[str] = None,
    ) -> ModelVersion:
        """Create a new model version."""
        model = _models_db.get(model_id)
        if not model:
            raise ModelNotFoundError(f"Model {model_id} not found")
        
        # Get previous version
        prev_versions = [v for v in _versions_db.values() if v.model_id == model_id]
        parent_id = prev_versions[-1].id if prev_versions else None
        
        ver = ModelVersion(
            id=str(uuid4()),
            model_id=model_id,
            version=version,
            model_hash=model_hash,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            metrics=metrics or {},
            changelog=changelog,
            parent_version_id=parent_id,
        )
        _versions_db[ver.id] = ver
        
        # Update model version
        model.version = version
        model.model_hash = model_hash
        if metrics:
            model.metrics.update(metrics)
        model.updated_at = datetime.now(timezone.utc)
        
        return ver
    
    @staticmethod
    async def get_versions(model_id: str) -> list[ModelVersion]:
        """Get all versions of a model."""
        return [v for v in _versions_db.values() if v.model_id == model_id]
    
    @staticmethod
    async def get_version(version_id: str) -> Optional[ModelVersion]:
        """Get a specific version."""
        return _versions_db.get(version_id)
    
    @staticmethod
    async def count(org_id: Optional[str] = None) -> int:
        """Count models, optionally filtered by organization."""
        if org_id:
            return sum(1 for m in _models_db.values() if m.org_id == org_id)
        return len(_models_db)


# Singleton instance
models_service = ModelsService()
