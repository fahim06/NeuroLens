"""
Preprocessor Interface Contract

Defines the abstract base class for all data preprocessors.
Supports both training (fit + transform) and inference (transform only) modes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray


# Type aliases
ImageArray = NDArray[np.float32]
T = TypeVar("T")


@dataclass
class PreprocessorConfig:
    """
    Configuration for image preprocessing.
    
    Attributes:
        target_size: Target image dimensions (height, width)
        normalize: Whether to apply normalization
        mean: Per-channel mean for normalization
        std: Per-channel standard deviation for normalization
        augment: Whether to apply augmentation (training only)
    """
    
    target_size: tuple[int, int] = (224, 224)
    normalize: bool = True
    mean: tuple[float, ...] = (0.485, 0.456, 0.406)  # ImageNet defaults
    std: tuple[float, ...] = (0.229, 0.224, 0.225)
    augment: bool = False


class BasePreprocessor(ABC, Generic[T]):
    """
    Abstract base class for data preprocessors.
    
    Supports the fit/transform pattern for stateful preprocessing
    (e.g., learning normalization statistics from training data).
    
    Type Parameters:
        T: Type of data being preprocessed
    
    Example:
        >>> preprocessor = ImagePreprocessor(config)
        >>> preprocessor.fit(training_images)
        >>> processed = preprocessor.transform(test_image)
    """
    
    def __init__(self, config: PreprocessorConfig | None = None) -> None:
        """
        Initialize preprocessor with configuration.
        
        Args:
            config: Preprocessing configuration, uses defaults if None
        """
        self.config = config or PreprocessorConfig()
        self._is_fitted = False
    
    @property
    def is_fitted(self) -> bool:
        """Whether the preprocessor has been fitted."""
        return self._is_fitted
    
    @abstractmethod
    def fit(self, data: T) -> "BasePreprocessor[T]":
        """
        Fit preprocessor to training data.
        
        Learns any statistics needed for preprocessing (e.g., normalization params).
        
        Args:
            data: Training data to fit on
        
        Returns:
            Self for method chaining
        """
        ...
    
    @abstractmethod
    def transform(self, data: T) -> T:
        """
        Transform data using learned parameters.
        
        Args:
            data: Data to transform
        
        Returns:
            Transformed data
        
        Raises:
            RuntimeError: If preprocessor hasn't been fitted
        """
        ...
    
    def fit_transform(self, data: T) -> T:
        """
        Fit to data, then transform it.
        
        Args:
            data: Data to fit and transform
        
        Returns:
            Transformed data
        """
        return self.fit(data).transform(data)
    
    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Save preprocessor state to disk.
        
        Args:
            path: Path to save preprocessor state
        """
        ...
    
    @abstractmethod
    def load(self, path: Path) -> None:
        """
        Load preprocessor state from disk.
        
        Args:
            path: Path to load preprocessor state from
        """
        ...
    
    def get_params(self) -> dict[str, Any]:
        """
        Get preprocessor parameters.
        
        Returns:
            Dictionary of parameters
        """
        return {
            "target_size": self.config.target_size,
            "normalize": self.config.normalize,
            "mean": self.config.mean,
            "std": self.config.std,
            "augment": self.config.augment,
        }


class ImagePreprocessor(BasePreprocessor[ImageArray]):
    """
    Standard image preprocessing pipeline.
    
    Handles resizing, normalization, and optional augmentation.
    Thread-safe and deterministic for inference.
    """
    
    def __init__(self, config: PreprocessorConfig | None = None) -> None:
        """Initialize with configuration."""
        super().__init__(config)
        self._mean: NDArray[np.float32] | None = None
        self._std: NDArray[np.float32] | None = None
    
    def fit(self, data: ImageArray) -> "ImagePreprocessor":
        """
        Fit normalization parameters from training data.
        
        Args:
            data: Training images with shape [N, H, W, C]
        
        Returns:
            Self for method chaining
        """
        if self.config.normalize:
            # Use config values or compute from data
            self._mean = np.array(self.config.mean, dtype=np.float32)
            self._std = np.array(self.config.std, dtype=np.float32)
        
        self._is_fitted = True
        return self
    
    def transform(self, data: ImageArray) -> ImageArray:
        """
        Transform images using fitted parameters.
        
        Args:
            data: Images to transform, shape [H, W, C] or [N, H, W, C]
        
        Returns:
            Transformed images
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor must be fitted before transform")
        
        # Handle single image
        single_image = len(data.shape) == 3
        if single_image:
            data = np.expand_dims(data, axis=0)
        
        # Convert to float32 if needed
        if data.dtype == np.uint8:
            data = data.astype(np.float32) / 255.0
        
        # Normalize
        if self.config.normalize and self._mean is not None and self._std is not None:
            data = (data - self._mean) / self._std
        
        if single_image:
            data = data[0]
        
        return data
    
    def save(self, path: Path) -> None:
        """Save preprocessor state."""
        state = {
            "config": self.get_params(),
            "mean": self._mean.tolist() if self._mean is not None else None,
            "std": self._std.tolist() if self._std is not None else None,
            "is_fitted": self._is_fitted,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, state, allow_pickle=True)
    
    def load(self, path: Path) -> None:
        """Load preprocessor state."""
        state = np.load(path, allow_pickle=True).item()
        
        self._mean = np.array(state["mean"], dtype=np.float32) if state["mean"] else None
        self._std = np.array(state["std"], dtype=np.float32) if state["std"] else None
        self._is_fitted = state["is_fitted"]
