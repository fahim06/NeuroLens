"""
Preprocessing Pipeline

Standardized data preprocessing pipeline for both training and inference.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

from ml.core.interfaces.preprocessor import (
    BasePreprocessor,
    ImagePreprocessor,
    PreprocessorConfig,
)
from ml.core.schemas.input import ImageBatch, ImageInput


ImageArray = NDArray[np.float32]
TransformFn = Callable[[ImageArray], ImageArray]


@dataclass
class PipelineConfig:
    """
    Configuration for preprocessing pipeline.
    
    Attributes:
        preprocessor_config: Base preprocessor configuration
        augmentations: List of augmentation functions (training only)
        validation_enabled: Whether to validate inputs
        cache_enabled: Whether to cache transformed data
    """
    
    preprocessor_config: PreprocessorConfig = field(
        default_factory=PreprocessorConfig
    )
    augmentations: list[TransformFn] = field(default_factory=list)
    validation_enabled: bool = True
    cache_enabled: bool = False


class PreprocessingPipeline:
    """
    Unified preprocessing pipeline.
    
    Handles all preprocessing steps including:
    - Input validation
    - Resizing
    - Normalization
    - Augmentation (training only)
    
    Example:
        >>> pipeline = PreprocessingPipeline(config)
        >>> pipeline.fit(training_images)
        >>> processed = pipeline.transform(image)
    """
    
    def __init__(
        self,
        config: PipelineConfig | None = None,
        mode: str = "inference",
    ) -> None:
        """
        Initialize pipeline.
        
        Args:
            config: Pipeline configuration
            mode: "training" or "inference"
        """
        self.config = config or PipelineConfig()
        self.mode = mode
        
        # Initialize preprocessor
        self._preprocessor = ImagePreprocessor(
            self.config.preprocessor_config
        )
        self._is_fitted = False
    
    @property
    def is_fitted(self) -> bool:
        """Whether pipeline has been fitted."""
        return self._is_fitted
    
    def fit(self, data: ImageArray | ImageBatch) -> "PreprocessingPipeline":
        """
        Fit pipeline to training data.
        
        Args:
            data: Training images
        
        Returns:
            Self for method chaining
        """
        if isinstance(data, ImageBatch):
            data = data.to_array()
        
        self._preprocessor.fit(data)
        self._is_fitted = True
        return self
    
    def transform(
        self,
        data: ImageArray | ImageInput | ImageBatch,
    ) -> ImageArray:
        """
        Transform data through pipeline.
        
        Args:
            data: Input images
        
        Returns:
            Transformed images
        """
        if not self._is_fitted:
            raise RuntimeError("Pipeline must be fitted before transform")
        
        # Handle different input types
        if isinstance(data, ImageInput):
            array = data.data
        elif isinstance(data, ImageBatch):
            array = data.to_array()
        else:
            array = data
        
        # Validate if enabled
        if self.config.validation_enabled:
            self._validate_input(array)
        
        # Apply base preprocessing
        result = self._preprocessor.transform(array)
        
        # Apply augmentations in training mode
        if self.mode == "training" and self.config.augmentations:
            for aug_fn in self.config.augmentations:
                result = aug_fn(result)
        
        return result
    
    def fit_transform(
        self,
        data: ImageArray | ImageBatch,
    ) -> ImageArray:
        """Fit and transform in one step."""
        return self.fit(data).transform(data)
    
    def _validate_input(self, data: ImageArray) -> None:
        """
        Validate input data.
        
        Args:
            data: Input array to validate
        
        Raises:
            ValueError: If validation fails
        """
        if data.ndim not in (3, 4):
            raise ValueError(
                f"Expected 3D or 4D array, got shape {data.shape}"
            )
        
        # Check for NaN/Inf
        if np.isnan(data).any() or np.isinf(data).any():
            raise ValueError("Input contains NaN or Inf values")
    
    def save(self, path: Path) -> None:
        """
        Save pipeline state.
        
        Args:
            path: Path to save to
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "mode": self.mode,
            "is_fitted": self._is_fitted,
            "config": {
                "target_size": self.config.preprocessor_config.target_size,
                "normalize": self.config.preprocessor_config.normalize,
                "mean": self.config.preprocessor_config.mean,
                "std": self.config.preprocessor_config.std,
            },
        }
        
        # Save preprocessor separately
        preprocessor_path = path.parent / f"{path.stem}_preprocessor.npy"
        self._preprocessor.save(preprocessor_path)
        
        state["preprocessor_path"] = str(preprocessor_path)
        np.save(path, state, allow_pickle=True)
    
    def load(self, path: Path) -> None:
        """
        Load pipeline state.
        
        Args:
            path: Path to load from
        """
        state = np.load(path, allow_pickle=True).item()
        
        self.mode = state["mode"]
        self._is_fitted = state["is_fitted"]
        
        # Load preprocessor
        if "preprocessor_path" in state:
            self._preprocessor.load(Path(state["preprocessor_path"]))
    
    def freeze(self) -> "PreprocessingPipeline":
        """
        Create frozen copy for inference.
        
        Returns:
            New pipeline in inference mode
        """
        if not self._is_fitted:
            raise RuntimeError("Cannot freeze unfitted pipeline")
        
        frozen = PreprocessingPipeline(
            config=PipelineConfig(
                preprocessor_config=self.config.preprocessor_config,
                augmentations=[],  # No augmentations in inference
                validation_enabled=self.config.validation_enabled,
                cache_enabled=self.config.cache_enabled,
            ),
            mode="inference",
        )
        
        frozen._preprocessor = self._preprocessor
        frozen._is_fitted = True
        
        return frozen
