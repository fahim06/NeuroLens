"""
Inference Pipeline

Production-ready inference pipeline with frozen preprocessing.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ml.core.interfaces.model import BaseModel
from ml.core.schemas.input import ImageBatch, ImageInput
from ml.core.schemas.output import (
    BatchPredictionResult,
    ClassificationResult,
)
from ml.pipelines.preprocess import PreprocessingPipeline


ImageArray = NDArray[np.float32]


@dataclass
class InferencePipelineConfig:
    """
    Configuration for inference pipeline.
    
    Attributes:
        batch_size: Maximum batch size for inference
        top_k: Number of top predictions to return
        return_probabilities: Include full probability distribution
        validate_inputs: Validate inputs before processing
        timeout_seconds: Maximum time per inference
    """
    
    batch_size: int = 32
    top_k: int = 5
    return_probabilities: bool = True
    validate_inputs: bool = True
    timeout_seconds: float = 30.0


class InferencePipeline:
    """
    Production inference pipeline.
    
    Uses frozen preprocessor from training for consistent results.
    No training logic - pure prediction only.
    
    Flow:
        Input → Preprocess (frozen) → Predict → Postprocess
    
    Example:
        >>> pipeline = InferencePipeline.from_artifacts(model, artifacts_path)
        >>> result = pipeline.predict(image)
    """
    
    def __init__(
        self,
        model: BaseModel,
        preprocessor: PreprocessingPipeline,
        config: InferencePipelineConfig | None = None,
    ) -> None:
        """
        Initialize inference pipeline.
        
        Args:
            model: Trained model for inference
            preprocessor: Frozen preprocessing pipeline
            config: Pipeline configuration
        """
        self.model = model
        self.preprocessor = preprocessor
        self.config = config or InferencePipelineConfig()
        
        # Validate preprocessor is fitted
        if not preprocessor.is_fitted:
            raise ValueError("Preprocessor must be fitted")
        
        # Ensure inference mode
        if preprocessor.mode != "inference":
            self.preprocessor = preprocessor.freeze()
    
    @classmethod
    def from_artifacts(
        cls,
        model: BaseModel,
        artifacts_path: Path,
        config: InferencePipelineConfig | None = None,
    ) -> "InferencePipeline":
        """
        Load pipeline from saved artifacts.
        
        Args:
            model: Model instance (weights loaded separately)
            artifacts_path: Path to training artifacts
            config: Pipeline configuration
        
        Returns:
            Configured InferencePipeline
        """
        # Load preprocessor
        preprocessor = PreprocessingPipeline(mode="inference")
        preprocessor_path = artifacts_path / "preprocessor.npy"
        preprocessor.load(preprocessor_path)
        
        return cls(model, preprocessor, config)
    
    def predict(
        self,
        data: ImageArray | ImageInput,
    ) -> ClassificationResult:
        """
        Run inference on a single image.
        
        Args:
            data: Input image
        
        Returns:
            ClassificationResult with prediction
        """
        start_time = time.perf_counter()
        
        # Handle input types
        if isinstance(data, ImageInput):
            image = data.data
            image_id = data.source
        else:
            image = data
            image_id = ""
        
        # Validate
        if self.config.validate_inputs:
            self._validate_single(image)
        
        # Preprocess
        processed = self.preprocessor.transform(image)
        
        # Ensure batch dimension
        if processed.ndim == 3:
            processed = np.expand_dims(processed, axis=0)
        
        # Predict
        probabilities = self.model.predict(processed)[0]
        
        inference_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Create result
        result = ClassificationResult.from_probabilities(
            probabilities=probabilities,
            class_names=list(self.model.output_classes),
            top_k=self.config.top_k,
            model_name=self.model.name,
            model_version=self.model.version,
            inference_time_ms=inference_time_ms,
        )
        result.image_id = image_id
        
        return result
    
    def predict_batch(
        self,
        data: ImageArray | ImageBatch | list[ImageInput],
    ) -> BatchPredictionResult:
        """
        Run inference on a batch of images.
        
        Args:
            data: Batch of input images
        
        Returns:
            BatchPredictionResult with all predictions
        """
        start_time = time.perf_counter()
        
        # Handle input types
        if isinstance(data, ImageBatch):
            images = data.to_array()
            batch_id = data.batch_id
        elif isinstance(data, list):
            images = np.stack([img.data for img in data], axis=0)
            batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        else:
            images = data
            batch_id = ""
        
        # Process in chunks if needed
        results = []
        num_images = len(images)
        
        for i in range(0, num_images, self.config.batch_size):
            chunk = images[i:i + self.config.batch_size]
            
            # Preprocess
            processed = self.preprocessor.transform(chunk)
            
            # Predict
            probabilities = self.model.predict(processed)
            
            # Create results for each image
            for j, probs in enumerate(probabilities):
                result = ClassificationResult.from_probabilities(
                    probabilities=probs,
                    class_names=list(self.model.output_classes),
                    top_k=self.config.top_k,
                    model_name=self.model.name,
                    model_version=self.model.version,
                )
                result.image_id = f"{batch_id}_{i + j}"
                results.append(result)
        
        total_time_ms = (time.perf_counter() - start_time) * 1000
        
        return BatchPredictionResult(
            results=results,
            batch_id=batch_id,
            total_inference_time_ms=total_time_ms,
            model_name=self.model.name,
            model_version=self.model.version,
        )
    
    def _validate_single(self, image: ImageArray) -> None:
        """Validate single image input."""
        if image.ndim != 3:
            raise ValueError(f"Expected 3D image [H, W, C], got {image.shape}")
        
        expected_shape = self.model.input_shape
        if image.shape != expected_shape:
            raise ValueError(
                f"Expected shape {expected_shape}, got {image.shape}"
            )
    
    def warm_up(self, num_iterations: int = 3) -> None:
        """
        Warm up pipeline with dummy predictions.
        
        Useful for consistent latency measurements.
        
        Args:
            num_iterations: Number of warm-up iterations
        """
        dummy_shape = (1,) + self.model.input_shape
        dummy_input = np.zeros(dummy_shape, dtype=np.float32)
        
        for _ in range(num_iterations):
            self.model.predict(dummy_input)
    
    def get_info(self) -> dict[str, Any]:
        """Get pipeline information."""
        return {
            "model_name": self.model.name,
            "model_version": self.model.version,
            "input_shape": self.model.input_shape,
            "output_classes": list(self.model.output_classes),
            "num_classes": len(self.model.output_classes),
            "batch_size": self.config.batch_size,
            "top_k": self.config.top_k,
        }
