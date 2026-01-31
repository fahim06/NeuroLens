"""
Postprocessor

Output post-processing for inference results.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)


@dataclass
class PredictionOutput:
    """
    Structured prediction output.
    
    Attributes:
        class_idx: Predicted class index
        class_name: Predicted class name
        confidence: Confidence score (calibrated if available)
        raw_confidence: Raw model confidence
        probabilities: All class probabilities
        class_names: All class names
        is_calibrated: Whether confidence is calibrated
    """
    
    class_idx: int
    class_name: str
    confidence: float
    raw_confidence: float
    probabilities: NDArray[np.float32]
    class_names: list[str]
    is_calibrated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "class_idx": self.class_idx,
            "class_name": self.class_name,
            "confidence": float(self.confidence),
            "raw_confidence": float(self.raw_confidence),
            "probabilities": {
                name: float(prob)
                for name, prob in zip(self.class_names, self.probabilities)
            },
            "is_calibrated": self.is_calibrated,
            "metadata": self.metadata,
        }
    
    @property
    def top_k(self) -> list[tuple[str, float]]:
        """Get top-k predictions."""
        indices = np.argsort(self.probabilities)[::-1]
        return [
            (self.class_names[idx], float(self.probabilities[idx]))
            for idx in indices
        ]


class Postprocessor:
    """
    Postprocessor for model outputs.
    
    Features:
    - Convert logits to probabilities
    - Apply temperature scaling
    - Generate structured outputs
    - Top-k predictions
    
    Example:
        >>> postprocessor = Postprocessor(class_names=["Normal", "Tumor"])
        >>> output = postprocessor.process(model_output)
        >>> print(output.class_name, output.confidence)
    """
    
    def __init__(
        self,
        class_names: list[str],
        confidence_threshold: float = 0.0,
        apply_softmax: bool = False,
    ) -> None:
        """
        Initialize postprocessor.
        
        Args:
            class_names: List of class names
            confidence_threshold: Minimum confidence threshold
            apply_softmax: Whether to apply softmax to outputs
        """
        self.class_names = class_names
        self.confidence_threshold = confidence_threshold
        self.apply_softmax = apply_softmax
    
    def process(
        self,
        output: NDArray[np.float32],
        calibration_temperature: float = 1.0,
    ) -> PredictionOutput:
        """
        Process single prediction output.
        
        Args:
            output: Model output (1D array of probabilities/logits)
            calibration_temperature: Temperature for calibration
        
        Returns:
            PredictionOutput with all information
        """
        # Ensure 1D
        if output.ndim > 1:
            output = output.squeeze()
        
        # Apply softmax if needed
        if self.apply_softmax:
            output = self._softmax(output)
        
        raw_confidence = float(np.max(output))
        
        # Apply temperature scaling
        if calibration_temperature != 1.0:
            calibrated = self._apply_temperature(output, calibration_temperature)
            is_calibrated = True
        else:
            calibrated = output
            is_calibrated = False
        
        # Get prediction
        class_idx = int(np.argmax(calibrated))
        confidence = float(calibrated[class_idx])
        
        return PredictionOutput(
            class_idx=class_idx,
            class_name=self.class_names[class_idx],
            confidence=confidence,
            raw_confidence=raw_confidence,
            probabilities=calibrated,
            class_names=self.class_names,
            is_calibrated=is_calibrated,
        )
    
    def process_batch(
        self,
        outputs: NDArray[np.float32],
        calibration_temperature: float = 1.0,
    ) -> list[PredictionOutput]:
        """
        Process batch of predictions.
        
        Args:
            outputs: Batch of model outputs
            calibration_temperature: Temperature for calibration
        
        Returns:
            List of PredictionOutput
        """
        return [
            self.process(output, calibration_temperature)
            for output in outputs
        ]
    
    def get_top_k(
        self,
        output: NDArray[np.float32],
        k: int = 5,
    ) -> list[tuple[int, str, float]]:
        """
        Get top-k predictions.
        
        Args:
            output: Model output
            k: Number of top predictions
        
        Returns:
            List of (class_idx, class_name, probability)
        """
        if output.ndim > 1:
            output = output.squeeze()
        
        if self.apply_softmax:
            output = self._softmax(output)
        
        indices = np.argsort(output)[::-1][:k]
        
        return [
            (int(idx), self.class_names[idx], float(output[idx]))
            for idx in indices
        ]
    
    def _softmax(self, x: NDArray[np.float32]) -> NDArray[np.float32]:
        """Apply softmax to logits."""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    def _apply_temperature(
        self,
        probabilities: NDArray[np.float32],
        temperature: float,
    ) -> NDArray[np.float32]:
        """Apply temperature scaling to probabilities."""
        # Convert to logits, scale, convert back
        logits = np.log(probabilities + 1e-10)
        scaled_logits = logits / temperature
        return self._softmax(scaled_logits)
