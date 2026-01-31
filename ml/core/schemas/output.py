"""
Output Schemas

Defines validated output data structures from the ML pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class PredictionOutput:
    """
    Single class prediction output.
    
    Attributes:
        class_name: Predicted class label
        class_index: Predicted class index
        confidence: Prediction confidence [0, 1]
        probabilities: Full probability distribution
    """
    
    class_name: str
    class_index: int
    confidence: float
    probabilities: tuple[float, ...]
    
    def __post_init__(self) -> None:
        """Validate prediction values."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0, 1], got {self.confidence}")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "class_name": self.class_name,
            "class_index": self.class_index,
            "confidence": self.confidence,
            "probabilities": list(self.probabilities),
        }


@dataclass
class ClassificationResult:
    """
    Complete classification result for a single image.
    
    Attributes:
        prediction: Primary prediction
        top_k: Top-k predictions ordered by confidence
        inference_time_ms: Inference time in milliseconds
        model_name: Name of model used
        model_version: Version of model used
        image_id: Identifier for the input image
        timestamp: Prediction timestamp
    """
    
    prediction: PredictionOutput
    top_k: list[PredictionOutput] = field(default_factory=list)
    inference_time_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""
    image_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def class_name(self) -> str:
        """Shortcut to predicted class name."""
        return self.prediction.class_name
    
    @property
    def confidence(self) -> float:
        """Shortcut to prediction confidence."""
        return self.prediction.confidence
    
    @classmethod
    def from_probabilities(
        cls,
        probabilities: NDArray[np.float32],
        class_names: list[str],
        top_k: int = 5,
        model_name: str = "",
        model_version: str = "",
        inference_time_ms: float = 0.0,
    ) -> "ClassificationResult":
        """
        Create result from raw probabilities.
        
        Args:
            probabilities: Probability array [num_classes]
            class_names: List of class names
            top_k: Number of top predictions to include
            model_name: Model identifier
            model_version: Model version
            inference_time_ms: Inference time
        
        Returns:
            ClassificationResult with top-k predictions
        """
        # Get sorted indices
        sorted_indices = np.argsort(probabilities)[::-1]
        
        # Build predictions
        predictions = []
        for idx in sorted_indices[:top_k]:
            pred = PredictionOutput(
                class_name=class_names[idx],
                class_index=int(idx),
                confidence=float(probabilities[idx]),
                probabilities=tuple(probabilities.tolist()),
            )
            predictions.append(pred)
        
        return cls(
            prediction=predictions[0],
            top_k=predictions,
            model_name=model_name,
            model_version=model_version,
            inference_time_ms=inference_time_ms,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prediction": self.prediction.to_dict(),
            "top_k": [p.to_dict() for p in self.top_k],
            "inference_time_ms": self.inference_time_ms,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "image_id": self.image_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BatchPredictionResult:
    """
    Results for a batch of predictions.
    
    Attributes:
        results: List of individual classification results
        batch_id: Batch identifier
        total_inference_time_ms: Total time for batch
        model_name: Model used
        model_version: Model version
    """
    
    results: list[ClassificationResult]
    batch_id: str = ""
    total_inference_time_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""
    
    def __len__(self) -> int:
        """Number of results."""
        return len(self.results)
    
    def __iter__(self):
        """Iterate over results."""
        return iter(self.results)
    
    def __getitem__(self, index: int) -> ClassificationResult:
        """Get result by index."""
        return self.results[index]
    
    @property
    def avg_inference_time_ms(self) -> float:
        """Average inference time per image."""
        if not self.results:
            return 0.0
        return self.total_inference_time_ms / len(self.results)
    
    @property
    def predictions(self) -> list[str]:
        """List of predicted class names."""
        return [r.class_name for r in self.results]
    
    @property
    def confidences(self) -> list[float]:
        """List of prediction confidences."""
        return [r.confidence for r in self.results]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "batch_id": self.batch_id,
            "total_inference_time_ms": self.total_inference_time_ms,
            "avg_inference_time_ms": self.avg_inference_time_ms,
            "model_name": self.model_name,
            "model_version": self.model_version,
        }
