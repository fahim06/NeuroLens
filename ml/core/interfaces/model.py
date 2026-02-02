"""
Model Interface Contract

Defines the abstract base class for all NeuroLens models.
Framework-agnostic interface that can wrap TensorFlow, PyTorch, or other backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray


# Type aliases
ImageArray = NDArray[np.float32]
PredictionArray = NDArray[np.float32]


@dataclass(frozen=True)
class ModelMetadata:
    """
    Immutable metadata describing a model.
    
    Attributes:
        name: Model identifier
        version: Semantic version string
        framework: Underlying framework (tensorflow, pytorch, etc.)
        input_shape: Expected input shape (H, W, C)
        output_classes: List of class labels
        created_at: Creation timestamp
        dataset_hash: Hash of training dataset for reproducibility
        extra: Additional metadata
    """
    
    name: str
    version: str
    framework: str
    input_shape: tuple[int, ...]
    output_classes: tuple[str, ...]
    created_at: datetime = field(default_factory=datetime.utcnow)
    dataset_hash: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    
    @property
    def num_classes(self) -> int:
        """Number of output classes."""
        return len(self.output_classes)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "framework": self.framework,
            "input_shape": list(self.input_shape),
            "output_classes": list(self.output_classes),
            "created_at": self.created_at.isoformat(),
            "dataset_hash": self.dataset_hash,
            "extra": self.extra,
        }


class BaseModel(ABC):
    """
    Abstract base class for all NeuroLens models.
    
    Enforces consistent interface across model implementations.
    All concrete models must inherit from this class.
    
    Example:
        >>> class TumorClassifier(BaseModel):
        ...     @property
        ...     def metadata(self) -> ModelMetadata:
        ...         return ModelMetadata(
        ...             name="tumor-classifier",
        ...             version="1.0.0",
        ...             framework="tensorflow",
        ...             input_shape=(224, 224, 3),
        ...             output_classes=("benign", "malignant"),
        ...         )
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """
        Model metadata including name, version, and configuration.
        
        Returns:
            ModelMetadata: Immutable model metadata
        """
        ...
    
    @property
    def name(self) -> str:
        """Model name shortcut."""
        return self.metadata.name
    
    @property
    def version(self) -> str:
        """Model version shortcut."""
        return self.metadata.version
    
    @property
    def input_shape(self) -> tuple[int, ...]:
        """Expected input shape (excluding batch dimension)."""
        return self.metadata.input_shape
    
    @property
    def output_classes(self) -> tuple[str, ...]:
        """List of output class names."""
        return self.metadata.output_classes
    
    @abstractmethod
    def predict(self, images: ImageArray) -> PredictionArray:
        """
        Run inference on a batch of images.
        
        Args:
            images: Batch of preprocessed images with shape [N, H, W, C]
        
        Returns:
            Prediction probabilities with shape [N, num_classes]
        
        Raises:
            ValueError: If images have incorrect shape
        """
        ...
    
    def predict_single(self, image: ImageArray) -> PredictionArray:
        """
        Run inference on a single image.
        
        Args:
            image: Single preprocessed image with shape [H, W, C]
        
        Returns:
            Prediction probabilities with shape [num_classes]
        """
        batch = np.expand_dims(image, axis=0)
        return self.predict(batch)[0]
    
    @abstractmethod
    def load(self, path: Path) -> None:
        """
        Load model weights from path.
        
        Args:
            path: Path to model weights file
        
        Raises:
            FileNotFoundError: If weights file doesn't exist
            ValueError: If weights are incompatible
        """
        ...
    
    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Save model weights to path.
        
        Args:
            path: Path to save weights file
        
        Raises:
            IOError: If save fails
        """
        ...
    
    def validate_input(self, images: ImageArray) -> None:
        """
        Validate input images match expected shape.
        
        Args:
            images: Batch of images to validate
        
        Raises:
            ValueError: If shape doesn't match
        """
        expected_shape = self.input_shape
        if len(images.shape) != 4:
            raise ValueError(
                f"Expected 4D batch [N, H, W, C], got shape {images.shape}"
            )
        
        actual_shape = images.shape[1:]
        if actual_shape != expected_shape:
            raise ValueError(
                f"Expected image shape {expected_shape}, got {actual_shape}"
            )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name!r}, version={self.version!r})"
