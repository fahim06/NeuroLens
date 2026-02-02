"""
ML Contracts Module

Defines explicit interfaces (protocols) for ML components.
These contracts enforce boundaries between services and ML core.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, TypeVar

import numpy as np
from numpy.typing import NDArray


# Type aliases
ImageArray = NDArray[np.float32]
PredictionDict = dict[str, Any]
MetricsDict = dict[str, float]
ConfigDict = dict[str, Any]

T = TypeVar("T")


class Preprocessor(Protocol):
    """Protocol for image preprocessing."""
    
    def __call__(self, image: ImageArray) -> ImageArray:
        """
        Preprocess an image for model input.
        
        Args:
            image: Raw image array
        
        Returns:
            Preprocessed image array
        """
        ...


class Postprocessor(Protocol):
    """Protocol for prediction postprocessing."""
    
    def __call__(
        self,
        predictions: NDArray[np.float32],
        class_names: list[str],
    ) -> list[PredictionDict]:
        """
        Postprocess model predictions.
        
        Args:
            predictions: Raw model output
            class_names: List of class labels
        
        Returns:
            List of prediction dictionaries
        """
        ...


class BaseModel(ABC):
    """
    Abstract base class for all NeuroLens models.
    
    Enforces consistent interface across model implementations.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Model name."""
        ...
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Model version (semantic versioning)."""
        ...
    
    @property
    @abstractmethod
    def input_shape(self) -> tuple[int, ...]:
        """Expected input shape (excluding batch dimension)."""
        ...
    
    @property
    @abstractmethod
    def output_classes(self) -> list[str]:
        """List of output class names."""
        ...
    
    @abstractmethod
    def predict(self, images: ImageArray) -> NDArray[np.float32]:
        """
        Run inference on batch of images.
        
        Args:
            images: Batch of preprocessed images [N, H, W, C]
        
        Returns:
            Prediction probabilities [N, num_classes]
        """
        ...
    
    @abstractmethod
    def load(self, path: Path) -> None:
        """
        Load model weights from path.
        
        Args:
            path: Path to model weights
        """
        ...
    
    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Save model weights to path.
        
        Args:
            path: Path to save weights
        """
        ...


class BaseTrainer(ABC):
    """
    Abstract base class for model trainers.
    
    Enforces consistent training interface.
    """
    
    @abstractmethod
    def train(
        self,
        train_data: Any,
        val_data: Any | None = None,
        config: ConfigDict | None = None,
    ) -> MetricsDict:
        """
        Train the model.
        
        Args:
            train_data: Training dataset
            val_data: Validation dataset
            config: Training configuration
        
        Returns:
            Final training metrics
        """
        ...
    
    @abstractmethod
    def evaluate(self, test_data: Any) -> MetricsDict:
        """
        Evaluate model on test data.
        
        Args:
            test_data: Test dataset
        
        Returns:
            Evaluation metrics
        """
        ...


class BaseExplainer(ABC):
    """
    Abstract base class for model explainability.
    
    Supports interpretability methods like GradCAM, SHAP, etc.
    """
    
    @abstractmethod
    def explain(
        self,
        model: BaseModel,
        image: ImageArray,
        target_class: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate explanation for a prediction.
        
        Args:
            model: The model to explain
            image: Input image
            target_class: Optional target class index
        
        Returns:
            Explanation data (heatmaps, attributions, etc.)
        """
        ...


class FeatureExtractor(Protocol):
    """Protocol for feature extraction."""
    
    def extract(self, image: ImageArray) -> NDArray[np.float32]:
        """
        Extract features from an image.
        
        Args:
            image: Preprocessed image
        
        Returns:
            Feature vector
        """
        ...
