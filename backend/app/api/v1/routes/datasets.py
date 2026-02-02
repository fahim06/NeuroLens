"""
NeuroLens Datasets API Routes

Endpoints for dataset management.
"""

from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query, UploadFile, File
from pydantic import BaseModel, Field

from app.services.datasets import datasets_service, DatasetNotFoundError
from app.services.orgs import orgs_service
from app.services.quotas import quotas_service, QuotaType, QuotaExceededError
from app.services.auth import auth_service, AuthenticationError
from app.models.dataset import DatasetCreate, DatasetUpdate, DatasetResponse, DatasetType, DatasetStatus


router = APIRouter(prefix="/datasets", tags=["Datasets"])


# Request/Response Schemas

class CreateDatasetRequest(BaseModel):
    """Create dataset request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    dataset_type: DatasetType = DatasetType.TRAINING
    tags: List[str] = Field(default_factory=list)


class UpdateDatasetRequest(BaseModel):
    """Update dataset request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DatasetListResponse(BaseModel):
    """Dataset list response."""
    datasets: List[DatasetResponse]
    total: int
    skip: int
    limit: int


class VersionResponse(BaseModel):
    """Dataset version response."""
    id: str
    version: str
    data_hash: str
    created_at: datetime
    created_by: str
    changelog: Optional[str] = None


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Dependency to get current user

async def get_current_user(authorization: str = Header(..., description="Bearer token")):
    """Get current authenticated user."""
    try:
        token = authorization.replace("Bearer ", "")
        return await auth_service.get_current_user(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Routes

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    request: CreateDatasetRequest,
    current_user=Depends(get_current_user),
):
    """
    Create a new dataset.
    
    Creates a dataset entry in the registry.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )
    
    # Check quota
    try:
        await quotas_service.consume_quota(
            org_id=current_user.org_id,
            quota_type=QuotaType.DATASETS,
        )
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Dataset quota exceeded: {e.usage.used}/{e.usage.limit}",
        )
    
    dataset_data = DatasetCreate(
        name=request.name,
        description=request.description,
        dataset_type=request.dataset_type,
        tags=request.tags,
    )
    
    dataset = await datasets_service.create(
        dataset_data,
        current_user.org_id,
        current_user.id,
    )
    
    # Update org usage
    await orgs_service.increment_usage(current_user.org_id, "datasets")
    
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        org_id=dataset.org_id,
        created_by=dataset.created_by,
        dataset_type=dataset.dataset_type,
        status=dataset.status,
        tags=dataset.tags,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    dataset_type: Optional[DatasetType] = Query(None, description="Filter by type"),
    status: Optional[DatasetStatus] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_user),
):
    """
    List datasets for the user's organization.
    """
    if not current_user.org_id:
        return DatasetListResponse(datasets=[], total=0, skip=skip, limit=limit)
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    datasets = await datasets_service.list(
        org_id=current_user.org_id,
        dataset_type=dataset_type,
        status=status,
        tags=tag_list,
        skip=skip,
        limit=limit,
    )
    total = await datasets_service.count(org_id=current_user.org_id)
    
    return DatasetListResponse(
        datasets=[
            DatasetResponse(
                id=d.id,
                name=d.name,
                description=d.description,
                org_id=d.org_id,
                created_by=d.created_by,
                dataset_type=d.dataset_type,
                status=d.status,
                tags=d.tags,
                version=d.version,
                num_samples=d.num_samples,
                num_classes=d.num_classes,
                size_mb=d.size_mb,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in datasets
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get dataset details.
    """
    try:
        dataset = await datasets_service.get(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    
    # Check org membership
    if dataset.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        org_id=dataset.org_id,
        created_by=dataset.created_by,
        dataset_type=dataset.dataset_type,
        status=dataset.status,
        tags=dataset.tags,
        version=dataset.version,
        data_hash=dataset.data_hash,
        num_samples=dataset.num_samples,
        num_classes=dataset.num_classes,
        class_names=dataset.class_names,
        class_distribution=dataset.class_distribution,
        size_mb=dataset.size_mb,
        file_count=dataset.file_count,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        last_validated_at=dataset.last_validated_at,
    )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    request: UpdateDatasetRequest,
    current_user=Depends(get_current_user),
):
    """
    Update dataset metadata.
    """
    try:
        dataset = await datasets_service.get(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    
    if dataset.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    update_data = DatasetUpdate(**request.model_dump(exclude_unset=True))
    dataset = await datasets_service.update(dataset_id, update_data)
    
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        org_id=dataset.org_id,
        created_by=dataset.created_by,
        dataset_type=dataset.dataset_type,
        status=dataset.status,
        tags=dataset.tags,
        version=dataset.version,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.delete("/{dataset_id}", response_model=MessageResponse)
async def delete_dataset(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete (archive) dataset.
    """
    try:
        dataset = await datasets_service.get(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    
    if dataset.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    await datasets_service.delete(dataset_id)
    return MessageResponse(message="Dataset archived successfully")


# Version management

@router.get("/{dataset_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    """
    List dataset versions.
    """
    try:
        dataset = await datasets_service.get(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    
    if dataset.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    versions = await datasets_service.get_versions(dataset_id)
    return [
        VersionResponse(
            id=v.id,
            version=v.version,
            data_hash=v.data_hash,
            created_at=v.created_at,
            created_by=v.created_by,
            changelog=v.changelog,
        )
        for v in versions
    ]


@router.post("/{dataset_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    dataset_id: str,
    version: str = Query(..., description="Version string (e.g., 1.0.0)"),
    data_hash: str = Query(..., description="Data hash for verification"),
    changelog: Optional[str] = Query(None, description="Version changelog"),
    current_user=Depends(get_current_user),
):
    """
    Create a new dataset version.
    """
    try:
        dataset = await datasets_service.get(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    
    if dataset.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    ver = await datasets_service.create_version(
        dataset_id,
        version,
        data_hash,
        current_user.id,
        changelog,
    )
    
    return VersionResponse(
        id=ver.id,
        version=ver.version,
        data_hash=ver.data_hash,
        created_at=ver.created_at,
        created_by=ver.created_by,
        changelog=ver.changelog,
    )


# Validation

@router.post("/{dataset_id}/validate", response_model=MessageResponse)
async def validate_dataset(
    dataset_id: str,
    current_user=Depends(get_current_user),
):
    """
    Trigger dataset validation.
    
    In production, this would start an async validation job.
    """
    try:
        dataset = await datasets_service.get(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )
    
    if dataset.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    # Mark as validating
    await datasets_service.set_validation_status(dataset_id, DatasetStatus.VALIDATING)
    
    return MessageResponse(message="Validation started")
