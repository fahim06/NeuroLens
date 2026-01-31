"""
Inference Schemas

Request and response models for inference endpoints.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionResult(BaseModel):
    """Single prediction result."""
    
    class_name: str = Field(..., description="Predicted class label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class InferenceRequest(BaseModel):
    """Inference request configuration."""
    
    model_id: str | None = Field(None, description="Specific model version to use")
    return_features: bool = Field(False, description="Whether to return extracted features")
    return_explainability: bool = Field(False, description="Whether to return explainability data")
    

class InferenceResponse(BaseModel):
    """Inference response with predictions."""
    
    request_id: UUID = Field(..., description="Unique request identifier")
    status: str = Field(..., description="Processing status")
    predictions: list[PredictionResult] = Field(..., description="Prediction results")
    model_id: str = Field(..., description="Model used for inference")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    features: dict[str, Any] | None = Field(None, description="Extracted features if requested")
    explainability: dict[str, Any] | None = Field(None, description="Explainability data if requested")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {"from_attributes": True}


class BatchInferenceResponse(BaseModel):
    """Batch inference job response."""
    
    batch_id: UUID = Field(..., description="Batch job identifier")
    status: str = Field(..., description="Batch job status")
    total_files: int = Field(..., description="Total number of files submitted")
    processed: int = Field(0, description="Number of files processed")
    failed: int = Field(0, description="Number of failed predictions")
