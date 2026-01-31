"""
Frozen Preprocessor

Stateless preprocessing pipeline for inference.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None


@dataclass
class PreprocessorConfig:
    """
    Preprocessing configuration.
    
    Attributes:
        target_size: Target image size (H, W)
        normalize: Whether to normalize to [0, 1]
        rescale: Rescaling factor (e.g., 1/255)
        mean: Per-channel mean for normalization
        std: Per-channel std for normalization
        preserve_aspect_ratio: Whether to preserve aspect ratio
        interpolation: Interpolation method
    """
    
    target_size: tuple[int, int] = (224, 224)
    normalize: bool = True
    rescale: float = 1.0 / 255.0
    mean: tuple[float, float, float] | None = None
    std: tuple[float, float, float] | None = None
    preserve_aspect_ratio: bool = False
    interpolation: str = "bilinear"
    
    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "PreprocessorConfig":
        """Create from dictionary."""
        return cls(
            target_size=tuple(config.get("target_size", [224, 224])),
            normalize=config.get("normalize", True),
            rescale=config.get("rescale", 1.0 / 255.0),
            mean=tuple(config["mean"]) if config.get("mean") else None,
            std=tuple(config["std"]) if config.get("std") else None,
            preserve_aspect_ratio=config.get("preserve_aspect_ratio", False),
            interpolation=config.get("interpolation", "bilinear"),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target_size": list(self.target_size),
            "normalize": self.normalize,
            "rescale": self.rescale,
            "mean": list(self.mean) if self.mean else None,
            "std": list(self.std) if self.std else None,
            "preserve_aspect_ratio": self.preserve_aspect_ratio,
            "interpolation": self.interpolation,
        }


class InferencePreprocessor:
    """
    Stateless preprocessing pipeline for inference.
    
    Features:
    - Frozen configuration (no mutable state)
    - Deterministic outputs for same inputs
    - Supports both numpy arrays and file paths
    
    Example:
        >>> config = PreprocessorConfig(target_size=(224, 224))
        >>> preprocessor = InferencePreprocessor(config)
        >>> image = preprocessor.process(image_array)
    """
    
    def __init__(self, config: PreprocessorConfig) -> None:
        """
        Initialize preprocessor.
        
        Args:
            config: Preprocessing configuration
        """
        self.config = config
        self._interpolation = self._get_interpolation_method()
    
    def _get_interpolation_method(self) -> str:
        """Get TensorFlow interpolation method."""
        methods = {
            "bilinear": "bilinear",
            "nearest": "nearest",
            "bicubic": "bicubic",
            "lanczos3": "lanczos3",
            "lanczos5": "lanczos5",
        }
        return methods.get(self.config.interpolation, "bilinear")
    
    def process(
        self,
        image: NDArray[np.uint8] | NDArray[np.float32] | str | Path,
    ) -> NDArray[np.float32]:
        """
        Process a single image for inference.
        
        Args:
            image: Image as numpy array or file path
        
        Returns:
            Preprocessed image as float32 array
        """
        # Load image if path
        if isinstance(image, (str, Path)):
            image = self._load_image(Path(image))
        
        # Convert to float32
        if image.dtype == np.uint8:
            image = image.astype(np.float32)
        
        # Resize
        image = self._resize(image)
        
        # Normalize
        if self.config.normalize:
            image = self._normalize(image)
        
        return image
    
    def process_batch(
        self,
        images: list[NDArray[np.uint8] | NDArray[np.float32] | str | Path],
    ) -> NDArray[np.float32]:
        """
        Process a batch of images.
        
        Args:
            images: List of images or file paths
        
        Returns:
            Batch of preprocessed images
        """
        processed = [self.process(img) for img in images]
        return np.stack(processed, axis=0)
    
    def _load_image(self, path: Path) -> NDArray[np.uint8]:
        """Load image from file."""
        if HAS_TF:
            # Use TensorFlow for consistent loading
            raw = tf.io.read_file(str(path))
            image = tf.image.decode_image(raw, channels=3)
            return image.numpy()
        else:
            # Fallback to PIL
            from PIL import Image
            img = Image.open(path).convert("RGB")
            return np.array(img)
    
    def _resize(self, image: NDArray[np.float32]) -> NDArray[np.float32]:
        """Resize image to target size."""
        target_h, target_w = self.config.target_size
        
        if HAS_TF:
            if self.config.preserve_aspect_ratio:
                # Resize with padding
                image = tf.image.resize_with_pad(
                    image,
                    target_h,
                    target_w,
                    method=self._interpolation,
                )
            else:
                image = tf.image.resize(
                    image,
                    [target_h, target_w],
                    method=self._interpolation,
                )
            return image.numpy()
        else:
            # Fallback to PIL
            from PIL import Image
            img = Image.fromarray(image.astype(np.uint8))
            img = img.resize((target_w, target_h), Image.BILINEAR)
            return np.array(img).astype(np.float32)
    
    def _normalize(self, image: NDArray[np.float32]) -> NDArray[np.float32]:
        """Normalize image values."""
        # Apply rescaling
        image = image * self.config.rescale
        
        # Apply mean/std normalization if specified
        if self.config.mean is not None:
            mean = np.array(self.config.mean, dtype=np.float32)
            image = image - mean
        
        if self.config.std is not None:
            std = np.array(self.config.std, dtype=np.float32)
            image = image / (std + 1e-7)
        
        return image
    
    def inverse_normalize(
        self,
        image: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """
        Reverse normalization for visualization.
        
        Args:
            image: Normalized image
        
        Returns:
            De-normalized image in [0, 255] range
        """
        if self.config.std is not None:
            std = np.array(self.config.std, dtype=np.float32)
            image = image * std
        
        if self.config.mean is not None:
            mean = np.array(self.config.mean, dtype=np.float32)
            image = image + mean
        
        # Reverse rescaling
        if self.config.rescale != 0:
            image = image / self.config.rescale
        
        return np.clip(image, 0, 255)
