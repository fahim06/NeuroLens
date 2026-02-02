"""
NeuroLens Models API Routes

Endpoints for ML model registry management.
"""

from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from pydantic import BaseModel, Field

from app.services.models import models_service, ModelNotFoundError
from app.services.orgs import orgs_service
from app.services.quotas import quotas_service, QuotaType, QuotaExceededError
from app.services.auth import auth_service, AuthenticationError
from app.models.ml_model import ModelCreate, ModelUpdate, ModelResponse, ModelType, ModelStatus


router = APIRouter(prefix="/models", tags=["Models"])


# Request/Response Schemas

class CreateModelRequest(BaseModel):
    """Create model request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    model_type: ModelType = ModelType.CLASSIFICATION
    framework: str = "tensorflow"
    tags: List[str] = Field(default_factory=list)


class UpdateModelRequest(BaseModel):
    """Update model request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ModelListResponse(BaseModel):
    """Model list response."""
    models: List[ModelResponse]
    total: int
    skip: int
    limit: int


class VersionResponse(BaseModel):
    """Model version response."""
    id: str
    version: str
    model_hash: str
    created_at: datetime
    created_by: str
    metrics: dict = Field(default_factory=dict)
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

@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    request: CreateModelRequest,
    current_user=Depends(get_current_user),
):
    """
    Create a new model registry entry.
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
            quota_type=QuotaType.MODELS,
        )
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Model quota exceeded: {e.usage.used}/{e.usage.limit}",
        )
    
    model_data = ModelCreate(
        name=request.name,
        description=request.description,
        model_type=request.model_type,
        framework=request.framework,
        tags=request.tags,
    )
    
    model = await models_service.create(
        model_data,
        current_user.org_id,
        current_user.id,
    )
    
    # Update org usage
    await orgs_service.increment_usage(current_user.org_id, "models")
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        org_id=model.org_id,
        created_by=model.created_by,
        model_type=model.model_type,
        framework=model.framework,
        status=model.status,
        tags=model.tags,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get("", response_model=ModelListResponse)
async def list_models(
    model_type: Optional[ModelType] = Query(None, description="Filter by type"),
    status: Optional[ModelStatus] = Query(None, description="Filter by status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_user),
):
    """
    List models for the user's organization.
    """
    if not current_user.org_id:
        return ModelListResponse(models=[], total=0, skip=skip, limit=limit)
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    models = await models_service.list(
        org_id=current_user.org_id,
        model_type=model_type,
        status=status,
        tags=tag_list,
        skip=skip,
        limit=limit,
    )
    total = await models_service.count(org_id=current_user.org_id)
    
    return ModelListResponse(
        models=[
            ModelResponse(
                id=m.id,
                name=m.name,
                description=m.description,
                org_id=m.org_id,
                created_by=m.created_by,
                model_type=m.model_type,
                framework=m.framework,
                status=m.status,
                tags=m.tags,
                version=m.version,
                metrics=m.metrics,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/production", response_model=ModelResponse)
async def get_production_model(current_user=Depends(get_current_user)):
    """
    Get the production model for the organization.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )
    
    model = await models_service.get_production_model(current_user.org_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No production model found",
        )
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        org_id=model.org_id,
        created_by=model.created_by,
        model_type=model.model_type,
        framework=model.framework,
        status=model.status,
        tags=model.tags,
        version=model.version,
        metrics=model.metrics,
        artifact_path=model.artifact_path,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    current_user=Depends(get_current_user),
):
    """
    Get model details.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        org_id=model.org_id,
        created_by=model.created_by,
        model_type=model.model_type,
        framework=model.framework,
        status=model.status,
        tags=model.tags,
        version=model.version,
        model_hash=model.model_hash,
        metrics=model.metrics,
        artifact_path=model.artifact_path,
        training_dataset_id=model.training_dataset_id,
        training_config=model.training_config,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    request: UpdateModelRequest,
    current_user=Depends(get_current_user),
):
    """
    Update model metadata.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    update_data = ModelUpdate(**request.model_dump(exclude_unset=True))
    model = await models_service.update(model_id, update_data)
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        org_id=model.org_id,
        created_by=model.created_by,
        model_type=model.model_type,
        framework=model.framework,
        status=model.status,
        tags=model.tags,
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.delete("/{model_id}", response_model=MessageResponse)
async def delete_model(
    model_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete (archive) model.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    await models_service.delete(model_id)
    return MessageResponse(message="Model archived successfully")


# Status management

@router.post("/{model_id}/promote", response_model=ModelResponse)
async def promote_to_production(
    model_id: str,
    current_user=Depends(get_current_user),
):
    """
    Promote model to production.
    
    Demotes any existing production model to staged.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    model = await models_service.set_status(model_id, ModelStatus.PRODUCTION)
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        org_id=model.org_id,
        created_by=model.created_by,
        model_type=model.model_type,
        framework=model.framework,
        status=model.status,
        tags=model.tags,
        version=model.version,
        metrics=model.metrics,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@router.post("/{model_id}/stage", response_model=ModelResponse)
async def stage_model(
    model_id: str,
    current_user=Depends(get_current_user),
):
    """
    Stage model for testing before production.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    model = await models_service.set_status(model_id, ModelStatus.STAGED)
    
    return ModelResponse(
        id=model.id,
        name=model.name,
        description=model.description,
        org_id=model.org_id,
        created_by=model.created_by,
        model_type=model.model_type,
        framework=model.framework,
        status=model.status,
        tags=model.tags,
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


# Version management

@router.get("/{model_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    model_id: str,
    current_user=Depends(get_current_user),
):
    """
    List model versions.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    versions = await models_service.get_versions(model_id)
    return [
        VersionResponse(
            id=v.id,
            version=v.version,
            model_hash=v.model_hash,
            created_at=v.created_at,
            created_by=v.created_by,
            metrics=v.metrics,
            changelog=v.changelog,
        )
        for v in versions
    ]


@router.post("/{model_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    model_id: str,
    version: str = Query(..., description="Version string"),
    model_hash: str = Query(..., description="Model hash"),
    changelog: Optional[str] = Query(None, description="Version changelog"),
    current_user=Depends(get_current_user),
):
    """
    Create a new model version.
    """
    try:
        model = await models_service.get(model_id)
    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    if model.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    ver = await models_service.create_version(
        model_id,
        version,
        model_hash,
        current_user.id,
        changelog=changelog,
    )
    
    return VersionResponse(
        id=ver.id,
        version=ver.version,
        model_hash=ver.model_hash,
        created_at=ver.created_at,
        created_by=ver.created_by,
        metrics=ver.metrics,
        changelog=ver.changelog,
    )
