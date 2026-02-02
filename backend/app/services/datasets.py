"""
NeuroLens Datasets Service

Dataset management service.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models.dataset import (
    Dataset,
    DatasetCreate,
    DatasetUpdate,
    DatasetVersion,
    DatasetStatus,
    DatasetType,
)


# In-memory storage (replace with database in production)
_datasets_db: dict[str, Dataset] = {}
_versions_db: dict[str, DatasetVersion] = {}


class DatasetNotFoundError(Exception):
    """Dataset not found error."""
    pass


class DatasetExistsError(Exception):
    """Dataset already exists error."""
    pass


class DatasetsService:
    """Datasets management service."""
    
    @staticmethod
    async def create(
        dataset_data: DatasetCreate,
        org_id: str,
        user_id: str,
    ) -> Dataset:
        """
        Create a new dataset.
        
        Args:
            dataset_data: Dataset creation data
            org_id: Organization ID
            user_id: Creator user ID
            
        Returns:
            Created dataset
        """
        dataset = Dataset(
            id=str(uuid4()),
            name=dataset_data.name,
            description=dataset_data.description,
            org_id=org_id,
            created_by=user_id,
            dataset_type=dataset_data.dataset_type,
            status=DatasetStatus.DRAFT,
            tags=dataset_data.tags,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        _datasets_db[dataset.id] = dataset
        return dataset
    
    @staticmethod
    async def get(dataset_id: str) -> Dataset:
        """
        Get dataset by ID.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dataset
            
        Raises:
            DatasetNotFoundError: If dataset not found
        """
        dataset = _datasets_db.get(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        return dataset
    
    @staticmethod
    async def list(
        org_id: Optional[str] = None,
        dataset_type: Optional[DatasetType] = None,
        status: Optional[DatasetStatus] = None,
        tags: Optional[list[str]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Dataset]:
        """
        List datasets with optional filters.
        
        Args:
            org_id: Filter by organization
            dataset_type: Filter by type
            status: Filter by status
            tags: Filter by tags (any match)
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of datasets
        """
        datasets = list(_datasets_db.values())
        
        if org_id:
            datasets = [d for d in datasets if d.org_id == org_id]
        if dataset_type:
            datasets = [d for d in datasets if d.dataset_type == dataset_type]
        if status:
            datasets = [d for d in datasets if d.status == status]
        if tags:
            datasets = [d for d in datasets if any(t in d.tags for t in tags)]
        
        return datasets[skip:skip + limit]
    
    @staticmethod
    async def update(dataset_id: str, update_data: DatasetUpdate) -> Dataset:
        """
        Update dataset.
        
        Args:
            dataset_id: Dataset ID
            update_data: Update data
            
        Returns:
            Updated dataset
        """
        dataset = _datasets_db.get(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(dataset, field, value)
        
        dataset.updated_at = datetime.now(timezone.utc)
        return dataset
    
    @staticmethod
    async def delete(dataset_id: str) -> None:
        """
        Delete dataset (soft delete by archiving).
        
        Args:
            dataset_id: Dataset ID
        """
        dataset = _datasets_db.get(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        
        dataset.status = DatasetStatus.ARCHIVED
        dataset.updated_at = datetime.now(timezone.utc)
    
    @staticmethod
    async def set_validation_status(
        dataset_id: str,
        status: DatasetStatus,
        report_id: Optional[str] = None,
    ) -> Dataset:
        """Update dataset validation status."""
        dataset = _datasets_db.get(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        
        dataset.status = status
        dataset.validation_report_id = report_id
        dataset.last_validated_at = datetime.now(timezone.utc)
        dataset.updated_at = datetime.now(timezone.utc)
        return dataset
    
    @staticmethod
    async def update_stats(
        dataset_id: str,
        num_samples: int,
        num_classes: int,
        class_names: list[str],
        class_distribution: dict[str, int],
        size_mb: float,
        file_count: int,
    ) -> Dataset:
        """Update dataset statistics."""
        dataset = _datasets_db.get(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        
        dataset.num_samples = num_samples
        dataset.num_classes = num_classes
        dataset.class_names = class_names
        dataset.class_distribution = class_distribution
        dataset.size_mb = size_mb
        dataset.file_count = file_count
        dataset.updated_at = datetime.now(timezone.utc)
        return dataset
    
    # Version management
    
    @staticmethod
    async def create_version(
        dataset_id: str,
        version: str,
        data_hash: str,
        user_id: str,
        changelog: Optional[str] = None,
    ) -> DatasetVersion:
        """Create a new dataset version."""
        dataset = _datasets_db.get(dataset_id)
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        
        # Get previous version
        prev_versions = [v for v in _versions_db.values() if v.dataset_id == dataset_id]
        parent_id = prev_versions[-1].id if prev_versions else None
        
        ver = DatasetVersion(
            id=str(uuid4()),
            dataset_id=dataset_id,
            version=version,
            data_hash=data_hash,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            changelog=changelog,
            parent_version_id=parent_id,
        )
        _versions_db[ver.id] = ver
        
        # Update dataset version
        dataset.version = version
        dataset.data_hash = data_hash
        dataset.updated_at = datetime.now(timezone.utc)
        
        return ver
    
    @staticmethod
    async def get_versions(dataset_id: str) -> list[DatasetVersion]:
        """Get all versions of a dataset."""
        return [v for v in _versions_db.values() if v.dataset_id == dataset_id]
    
    @staticmethod
    async def get_version(version_id: str) -> Optional[DatasetVersion]:
        """Get a specific version."""
        return _versions_db.get(version_id)
    
    @staticmethod
    async def count(org_id: Optional[str] = None) -> int:
        """Count datasets, optionally filtered by organization."""
        if org_id:
            return sum(1 for d in _datasets_db.values() if d.org_id == org_id)
        return len(_datasets_db)


# Singleton instance
datasets_service = DatasetsService()
