"""
Image Augmentation

Provides configurable image augmentation for training.
Supports both numpy-based and TensorFlow-based augmentations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)

# Type alias
ImageArray = NDArray[np.float32]
AugmentationFn = Callable[[ImageArray], ImageArray]


@dataclass
class AugmentationConfig:
    """
    Configuration for image augmentation.
    
    Attributes:
        horizontal_flip: Random horizontal flip
        vertical_flip: Random vertical flip
        rotation_range: Max rotation in degrees
        zoom_range: Zoom range (0.1 = ±10%)
        brightness_range: Brightness adjustment range
        shear_range: Shear transformation range
        width_shift_range: Horizontal shift range
        height_shift_range: Vertical shift range
        channel_shift_range: Channel shift range
        fill_mode: Fill mode for transformations
    """
    
    horizontal_flip: bool = True
    vertical_flip: bool = False
    rotation_range: float = 15.0
    zoom_range: float = 0.1
    brightness_range: tuple[float, float] = (0.9, 1.1)
    shear_range: float = 0.1
    width_shift_range: float = 0.1
    height_shift_range: float = 0.1
    channel_shift_range: float = 0.0
    fill_mode: str = "nearest"
    
    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "AugmentationConfig":
        """Create from dictionary."""
        return cls(
            horizontal_flip=config.get("horizontal_flip", True),
            vertical_flip=config.get("vertical_flip", False),
            rotation_range=config.get("rotation_range", 15.0),
            zoom_range=config.get("zoom_range", 0.1),
            brightness_range=tuple(config.get("brightness_range", (0.9, 1.1))),
            shear_range=config.get("shear_range", 0.1),
            width_shift_range=config.get("width_shift_range", 0.1),
            height_shift_range=config.get("height_shift_range", 0.1),
            channel_shift_range=config.get("channel_shift_range", 0.0),
            fill_mode=config.get("fill_mode", "nearest"),
        )
    
    @classmethod
    def none(cls) -> "AugmentationConfig":
        """No augmentation config."""
        return cls(
            horizontal_flip=False,
            vertical_flip=False,
            rotation_range=0.0,
            zoom_range=0.0,
            brightness_range=(1.0, 1.0),
            shear_range=0.0,
            width_shift_range=0.0,
            height_shift_range=0.0,
        )


class ImageAugmentor:
    """
    Applies image augmentations during training.
    
    Uses numpy for basic augmentations. For production, consider
    using albumentations or TensorFlow's image augmentation layers.
    
    Example:
        >>> config = AugmentationConfig(horizontal_flip=True, rotation_range=15)
        >>> augmentor = ImageAugmentor(config)
        >>> augmented = augmentor.augment(image)
    """
    
    def __init__(
        self,
        config: AugmentationConfig | None = None,
        seed: int | None = None,
    ) -> None:
        """
        Initialize augmentor.
        
        Args:
            config: Augmentation configuration
            seed: Random seed for reproducibility
        """
        self.config = config or AugmentationConfig()
        self.rng = np.random.default_rng(seed)
    
    def augment(self, image: ImageArray) -> ImageArray:
        """
        Apply augmentations to a single image.
        
        Args:
            image: Input image [H, W, C]
        
        Returns:
            Augmented image
        """
        result = image.copy()
        
        # Horizontal flip
        if self.config.horizontal_flip and self.rng.random() > 0.5:
            result = np.fliplr(result)
        
        # Vertical flip
        if self.config.vertical_flip and self.rng.random() > 0.5:
            result = np.flipud(result)
        
        # Rotation
        if self.config.rotation_range > 0:
            angle = self.rng.uniform(
                -self.config.rotation_range,
                self.config.rotation_range,
            )
            result = self._rotate(result, angle)
        
        # Brightness adjustment
        if self.config.brightness_range != (1.0, 1.0):
            factor = self.rng.uniform(*self.config.brightness_range)
            result = np.clip(result * factor, 0.0, 1.0)
        
        # Zoom
        if self.config.zoom_range > 0:
            zoom_factor = self.rng.uniform(
                1 - self.config.zoom_range,
                1 + self.config.zoom_range,
            )
            result = self._zoom(result, zoom_factor)
        
        # Shift
        if self.config.width_shift_range > 0 or self.config.height_shift_range > 0:
            result = self._shift(
                result,
                self.config.width_shift_range,
                self.config.height_shift_range,
            )
        
        return result.astype(np.float32)
    
    def augment_batch(self, images: ImageArray) -> ImageArray:
        """
        Apply augmentations to a batch of images.
        
        Args:
            images: Batch of images [N, H, W, C]
        
        Returns:
            Augmented batch
        """
        return np.array([self.augment(img) for img in images])
    
    def _rotate(self, image: ImageArray, angle: float) -> ImageArray:
        """
        Rotate image by angle degrees.
        
        Simple implementation using scipy if available,
        otherwise returns unrotated image.
        """
        try:
            from scipy.ndimage import rotate
            return rotate(
                image,
                angle,
                axes=(0, 1),
                reshape=False,
                mode="nearest",
            )
        except ImportError:
            logger.warning("scipy not available, skipping rotation")
            return image
    
    def _zoom(self, image: ImageArray, factor: float) -> ImageArray:
        """Apply zoom transformation."""
        h, w = image.shape[:2]
        
        # Calculate crop/pad size
        new_h = int(h / factor)
        new_w = int(w / factor)
        
        if factor > 1:
            # Zoom in: crop center
            start_h = (h - new_h) // 2
            start_w = (w - new_w) // 2
            cropped = image[start_h:start_h + new_h, start_w:start_w + new_w]
            
            # Resize back to original size
            return self._resize(cropped, (h, w))
        else:
            # Zoom out: pad and crop
            return image  # Simplified for now
    
    def _shift(
        self,
        image: ImageArray,
        width_range: float,
        height_range: float,
    ) -> ImageArray:
        """Apply random shift."""
        h, w = image.shape[:2]
        
        shift_h = int(h * self.rng.uniform(-height_range, height_range))
        shift_w = int(w * self.rng.uniform(-width_range, width_range))
        
        result = np.roll(image, shift_h, axis=0)
        result = np.roll(result, shift_w, axis=1)
        
        return result
    
    def _resize(
        self,
        image: ImageArray,
        target_size: tuple[int, int],
    ) -> ImageArray:
        """Resize image to target size."""
        try:
            from PIL import Image as PILImage
            
            pil_img = PILImage.fromarray((image * 255).astype(np.uint8))
            pil_img = pil_img.resize((target_size[1], target_size[0]))
            return np.array(pil_img, dtype=np.float32) / 255.0
        except ImportError:
            # Simple nearest neighbor resize
            h, w = target_size
            old_h, old_w = image.shape[:2]
            
            row_indices = (np.arange(h) * old_h // h).astype(int)
            col_indices = (np.arange(w) * old_w // w).astype(int)
            
            return image[row_indices][:, col_indices]


def create_augmentation_pipeline(
    config: dict[str, Any] | AugmentationConfig,
    seed: int = 42,
) -> ImageAugmentor:
    """
    Create augmentation pipeline from config.
    
    Args:
        config: Augmentation configuration (dict or AugmentationConfig)
        seed: Random seed
    
    Returns:
        Configured ImageAugmentor
    """
    if isinstance(config, dict):
        aug_config = AugmentationConfig.from_dict(config)
    else:
        aug_config = config
    
    return ImageAugmentor(aug_config, seed=seed)


def create_tf_augmentation_layer(
    config: AugmentationConfig,
) -> Any:
    """
    Create TensorFlow augmentation layer.
    
    Args:
        config: Augmentation configuration
    
    Returns:
        tf.keras.Sequential with augmentation layers
    """
    try:
        import tensorflow as tf
        
        layers = []
        
        if config.horizontal_flip:
            layers.append(tf.keras.layers.RandomFlip("horizontal"))
        
        if config.vertical_flip:
            layers.append(tf.keras.layers.RandomFlip("vertical"))
        
        if config.rotation_range > 0:
            # Convert degrees to fraction of 2*pi
            factor = config.rotation_range / 360.0
            layers.append(tf.keras.layers.RandomRotation(factor))
        
        if config.zoom_range > 0:
            layers.append(tf.keras.layers.RandomZoom(config.zoom_range))
        
        if config.brightness_range != (1.0, 1.0):
            # Convert to contrast factor
            factor = max(
                abs(1 - config.brightness_range[0]),
                abs(config.brightness_range[1] - 1),
            )
            if factor > 0:
                layers.append(tf.keras.layers.RandomBrightness(factor))
        
        if config.width_shift_range > 0 or config.height_shift_range > 0:
            layers.append(tf.keras.layers.RandomTranslation(
                config.height_shift_range,
                config.width_shift_range,
            ))
        
        return tf.keras.Sequential(layers, name="augmentation")
    
    except ImportError:
        raise ImportError("TensorFlow is required for TF augmentation layers")
