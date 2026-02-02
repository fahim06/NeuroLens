"""
NeuroLens Inference API Routes

Endpoints for model inference with authentication and quota enforcement.
"""

import base64
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Header, Query, UploadFile, File
from pydantic import BaseModel, Field

from app.services.models import models_service, ModelNotFoundError
from app.services.orgs import orgs_service
from app.services.quotas import quotas_service, QuotaType, QuotaExceededError
from app.services.auth import auth_service, AuthenticationError
from app.models.ml_model import ModelStatus


router = APIRouter(prefix="/inference", tags=["Inference"])


# Request/Response Schemas

class PredictionResult(BaseModel):
    """Single prediction result."""
    class_name: str
    confidence: float
    class_index: int


class InferenceResponse(BaseModel):
    """Inference response."""
    request_id: str
    model_id: str
    model_version: str
    predictions: List[PredictionResult]
    inference_time_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchPrediction(BaseModel):
    """Batch prediction item."""
    index: int
    predictions: List[PredictionResult]


class BatchInferenceResponse(BaseModel):
    """Batch inference response."""
    request_id: str
    model_id: str
    model_version: str
    batch_size: int
    results: List[BatchPrediction]
    total_inference_time_ms: float
    avg_inference_time_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuotaResponse(BaseModel):
    """Quota usage response."""
    quota_type: str
    used: int
    limit: int
    remaining: int
    reset_at: Optional[datetime] = None


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


# Helper to check and consume quota

async def check_inference_quota(org_id: str, count: int = 1):
    """Check and consume inference quota."""
    try:
        usage = await quotas_service.consume_quota(
            org_id=org_id,
            quota_type=QuotaType.INFERENCE_REQUESTS,
            amount=count,
        )
        return usage
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "quota_type": e.quota_type.value,
                "used": e.usage.used,
                "limit": e.usage.limit,
                "reset_at": e.usage.reset_at.isoformat() if e.usage.reset_at else None,
            },
        )


# Routes

@router.post("/predict", response_model=InferenceResponse)
async def predict(
    file: UploadFile = File(..., description="Image file to classify"),
    model_id: Optional[str] = Query(None, description="Model ID (uses production if not specified)"),
    top_k: int = Query(5, ge=1, le=20, description="Number of top predictions"),
    current_user=Depends(get_current_user),
):
    """
    Run inference on a single image.
    
    Uses the production model by default, or a specific model if provided.
    Requires authentication and consumes quota.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )
    
    # Check quota
    await check_inference_quota(current_user.org_id)
    
    # Get model
    if model_id:
        try:
            model = await models_service.get(model_id)
            if model.org_id != current_user.org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        except ModelNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )
    else:
        model = await models_service.get_production_model(current_user.org_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No production model found",
            )
    
    # Read image
    content = await file.read()
    
    # TODO: In production, this would call the actual ML inference service
    # For now, return mock predictions
    import uuid
    import random
    
    mock_classes = ["Alzheimer", "Mild Cognitive Impairment", "Normal", "Parkinson", "Dementia"]
    confidences = sorted([random.random() for _ in range(min(top_k, len(mock_classes)))], reverse=True)
    
    predictions = [
        PredictionResult(
            class_name=mock_classes[i % len(mock_classes)],
            confidence=confidences[i],
            class_index=i,
        )
        for i in range(min(top_k, len(mock_classes)))
    ]
    
    # Update API call count
    await orgs_service.increment_usage(current_user.org_id, "api_calls")
    
    return InferenceResponse(
        request_id=str(uuid.uuid4()),
        model_id=model.id,
        model_version=model.version or "1.0.0",
        predictions=predictions,
        inference_time_ms=random.uniform(50, 200),
    )


@router.post("/predict/batch", response_model=BatchInferenceResponse)
async def predict_batch(
    files: List[UploadFile] = File(..., description="Image files to classify"),
    model_id: Optional[str] = Query(None, description="Model ID (uses production if not specified)"),
    top_k: int = Query(5, ge=1, le=20, description="Number of top predictions per image"),
    current_user=Depends(get_current_user),
):
    """
    Run batch inference on multiple images.
    
    Uses the production model by default, or a specific model if provided.
    Batch size is limited by plan quota.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )
    
    batch_size = len(files)
    
    # Check batch size quota
    can_batch = await quotas_service.check_quota(
        org_id=current_user.org_id,
        quota_type=QuotaType.BATCH_SIZE,
        amount=batch_size,
    )
    if not can_batch:
        usage = await quotas_service.get_usage(org_id=current_user.org_id, quota_type=QuotaType.BATCH_SIZE)
        batch_limit = usage.get(QuotaType.BATCH_SIZE)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size {batch_size} exceeds limit of {batch_limit.limit if batch_limit else 10}",
        )
    
    # Check inference quota
    await check_inference_quota(current_user.org_id, batch_size)
    
    # Get model
    if model_id:
        try:
            model = await models_service.get(model_id)
            if model.org_id != current_user.org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        except ModelNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )
    else:
        model = await models_service.get_production_model(current_user.org_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No production model found",
            )
    
    # TODO: In production, this would call the actual ML inference service
    # For now, return mock predictions
    import uuid
    import random
    
    mock_classes = ["Alzheimer", "Mild Cognitive Impairment", "Normal", "Parkinson", "Dementia"]
    
    results = []
    total_time = 0
    
    for i, file in enumerate(files):
        content = await file.read()
        
        confidences = sorted([random.random() for _ in range(min(top_k, len(mock_classes)))], reverse=True)
        predictions = [
            PredictionResult(
                class_name=mock_classes[j % len(mock_classes)],
                confidence=confidences[j],
                class_index=j,
            )
            for j in range(min(top_k, len(mock_classes)))
        ]
        
        inference_time = random.uniform(30, 100)
        total_time += inference_time
        
        results.append(BatchPrediction(
            index=i,
            predictions=predictions,
        ))
    
    # Update API call count
    await orgs_service.increment_usage(current_user.org_id, "api_calls", batch_size)
    
    return BatchInferenceResponse(
        request_id=str(uuid.uuid4()),
        model_id=model.id,
        model_version=model.version or "1.0.0",
        batch_size=batch_size,
        results=results,
        total_inference_time_ms=total_time,
        avg_inference_time_ms=total_time / batch_size,
    )


@router.post("/predict/base64", response_model=InferenceResponse)
async def predict_base64(
    image_data: str = Query(..., description="Base64-encoded image data"),
    model_id: Optional[str] = Query(None, description="Model ID"),
    top_k: int = Query(5, ge=1, le=20),
    current_user=Depends(get_current_user),
):
    """
    Run inference on a base64-encoded image.
    
    Useful for API integrations where file upload is not convenient.
    """
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )
    
    # Check quota
    await check_inference_quota(current_user.org_id)
    
    # Decode image
    try:
        image_bytes = base64.b64decode(image_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 image data",
        )
    
    # Get model
    if model_id:
        try:
            model = await models_service.get(model_id)
            if model.org_id != current_user.org_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied",
                )
        except ModelNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found",
            )
    else:
        model = await models_service.get_production_model(current_user.org_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No production model found",
            )
    
    # TODO: In production, this would call the actual ML inference service
    import uuid
    import random
    
    mock_classes = ["Alzheimer", "Mild Cognitive Impairment", "Normal", "Parkinson", "Dementia"]
    confidences = sorted([random.random() for _ in range(min(top_k, len(mock_classes)))], reverse=True)
    
    predictions = [
        PredictionResult(
            class_name=mock_classes[i % len(mock_classes)],
            confidence=confidences[i],
            class_index=i,
        )
        for i in range(min(top_k, len(mock_classes)))
    ]
    
    # Update API call count
    await orgs_service.increment_usage(current_user.org_id, "api_calls")
    
    return InferenceResponse(
        request_id=str(uuid.uuid4()),
        model_id=model.id,
        model_version=model.version or "1.0.0",
        predictions=predictions,
        inference_time_ms=random.uniform(50, 200),
    )


@router.get("/quota", response_model=List[QuotaResponse])
async def get_quota(current_user=Depends(get_current_user)):
    """
    Get current inference quota usage.
    """
    if not current_user.org_id:
        return []
    
    usage = await quotas_service.get_usage(org_id=current_user.org_id)
    
    return [
        QuotaResponse(
            quota_type=qt.value,
            used=u.used,
            limit=u.limit,
            remaining=u.remaining,
            reset_at=u.reset_at,
        )
        for qt, u in usage.items()
    ]


@router.get("/models/available")
async def list_available_models(current_user=Depends(get_current_user)):
    """
    List models available for inference.
    
    Returns production and staged models.
    """
    if not current_user.org_id:
        return {"models": []}
    
    models = await models_service.list(org_id=current_user.org_id)
    
    # Filter to production and staged only
    available = [
        {
            "id": m.id,
            "name": m.name,
            "version": m.version,
            "status": m.status.value,
            "model_type": m.model_type.value,
            "metrics": m.metrics,
        }
        for m in models
        if m.status in (ModelStatus.PRODUCTION, ModelStatus.STAGED)
    ]
    
    return {"models": available}
