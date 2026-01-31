"""
Base Model Implementation

Provides a base classifier implementation that can be extended
for specific model architectures.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ml.core.interfaces.model import BaseModel, ModelMetadata


ImageArray = NDArray[np.float32]
PredictionArray = NDArray[np.float32]


class BaseClassifier(BaseModel):
    """
    Base image classifier implementation.
    
    Provides common functionality for classification models.
    Concrete implementations should override the _build_model
    and _load_weights methods.
    
    Example:
        >>> class TumorClassifier(BaseClassifier):
        ...     def _build_model(self):
        ...         # Build your model here
        ...         pass
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        input_shape: tuple[int, int, int],
        output_classes: tuple[str, ...],
        framework: str = "tensorflow",
    ) -> None:
        """
        Initialize classifier.
        
        Args:
            name: Model name
            version: Model version (semantic)
            input_shape: Expected input shape (H, W, C)
            output_classes: Output class labels
            framework: ML framework used
        """
        self._metadata = ModelMetadata(
            name=name,
            version=version,
            framework=framework,
            input_shape=input_shape,
            output_classes=output_classes,
        )
        
        self._model: Any = None
        self._is_loaded = False
    
    @property
    def metadata(self) -> ModelMetadata:
        """Model metadata."""
        return self._metadata
    
    @property
    def is_loaded(self) -> bool:
        """Whether model weights are loaded."""
        return self._is_loaded
    
    @abstractmethod
    def _build_model(self) -> Any:
        """
        Build the underlying model architecture.
        
        Returns:
            Built model object
        """
        ...
    
    @abstractmethod
    def _load_weights(self, path: Path) -> None:
        """
        Load weights into the model.
        
        Args:
            path: Path to weights file
        """
        ...
    
    @abstractmethod
    def _save_weights(self, path: Path) -> None:
        """
        Save model weights.
        
        Args:
            path: Path to save weights
        """
        ...
    
    def predict(self, images: ImageArray) -> PredictionArray:
        """
        Run inference on batch of images.
        
        Args:
            images: Batch of preprocessed images [N, H, W, C]
        
        Returns:
            Prediction probabilities [N, num_classes]
        """
        if not self._is_loaded:
            raise RuntimeError("Model weights not loaded")
        
        self.validate_input(images)
        
        return self._predict_impl(images)
    
    @abstractmethod
    def _predict_impl(self, images: ImageArray) -> PredictionArray:
        """
        Internal prediction implementation.
        
        Args:
            images: Validated batch of images
        
        Returns:
            Prediction probabilities
        """
        ...
    
    def load(self, path: Path) -> None:
        """
        Load model from path.
        
        Args:
            path: Path to model file
        """
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        
        if self._model is None:
            self._model = self._build_model()
        
        self._load_weights(path)
        self._is_loaded = True
    
    def save(self, path: Path) -> None:
        """
        Save model to path.
        
        Args:
            path: Path to save model
        """
        if self._model is None:
            raise RuntimeError("No model to save")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        self._save_weights(path)
    
    def get_class_name(self, index: int) -> str:
        """
        Get class name by index.
        
        Args:
            index: Class index
        
        Returns:
            Class name
        """
        return self.output_classes[index]
    
    def get_class_index(self, name: str) -> int:
        """
        Get class index by name.
        
        Args:
            name: Class name
        
        Returns:
            Class index
        """
        return self.output_classes.index(name)
