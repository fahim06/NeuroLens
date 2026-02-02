"""
Input Schemas

Defines validated input data structures for the ML pipeline.
All inputs are validated before processing to ensure data integrity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray


ImageArray = NDArray[np.float32]


@dataclass(frozen=True)
class ImageInput:
    """
    Validated single image input.
    
    Attributes:
        data: Image array with shape [H, W, C]
        source: Original source (path, URL, or "memory")
        format: Image format (png, jpg, etc.)
        original_size: Original dimensions before processing
        metadata: Additional metadata
    """
    
    data: ImageArray
    source: str = "memory"
    format: str = "unknown"
    original_size: tuple[int, int] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate input after creation."""
        if len(self.data.shape) != 3:
            raise ValueError(f"Expected 3D array [H, W, C], got shape {self.data.shape}")
        
        if self.data.shape[2] not in (1, 3, 4):
            raise ValueError(f"Expected 1, 3, or 4 channels, got {self.data.shape[2]}")
    
    @property
    def height(self) -> int:
        """Image height."""
        return int(self.data.shape[0])
    
    @property
    def width(self) -> int:
        """Image width."""
        return int(self.data.shape[1])
    
    @property
    def channels(self) -> int:
        """Number of channels."""
        return int(self.data.shape[2])
    
    @property
    def shape(self) -> tuple[int, int, int]:
        """Image shape as (H, W, C)."""
        return (self.height, self.width, self.channels)
    
    @classmethod
    def from_array(
        cls,
        array: NDArray[Any],
        source: str = "memory",
    ) -> "ImageInput":
        """
        Create from numpy array.
        
        Args:
            array: Image array, will be converted to float32
            source: Source identifier
        
        Returns:
            Validated ImageInput
        """
        # Convert to float32
        if array.dtype == np.uint8:
            data = array.astype(np.float32) / 255.0
        else:
            data = array.astype(np.float32)
        
        return cls(data=data, source=source)


@dataclass
class ImageBatch:
    """
    Validated batch of images.
    
    Attributes:
        images: List of ImageInput objects
        batch_id: Unique batch identifier
        created_at: Batch creation timestamp
    """
    
    images: list[ImageInput]
    batch_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Generate batch ID if not provided."""
        if not self.batch_id:
            object.__setattr__(
                self,
                "batch_id",
                f"batch_{self.created_at.strftime('%Y%m%d_%H%M%S')}",
            )
    
    def __len__(self) -> int:
        """Number of images in batch."""
        return len(self.images)
    
    def __iter__(self):
        """Iterate over images."""
        return iter(self.images)
    
    def to_array(self) -> ImageArray:
        """
        Convert batch to single numpy array.
        
        Returns:
            Array with shape [N, H, W, C]
        """
        return np.stack([img.data for img in self.images], axis=0)


@dataclass(frozen=True)
class DatasetInfo:
    """
    Metadata about a dataset.
    
    Attributes:
        name: Dataset identifier
        version: Dataset version
        num_samples: Total number of samples
        num_classes: Number of classes
        class_names: List of class labels
        split: Dataset split (train, val, test)
        hash: Content hash for reproducibility
        path: Path to dataset
    """
    
    name: str
    version: str
    num_samples: int
    num_classes: int
    class_names: tuple[str, ...]
    split: Literal["train", "val", "test", "all"] = "all"
    hash: str | None = None
    path: Path | None = None
    
    @property
    def class_distribution(self) -> dict[str, int] | None:
        """Class distribution if available."""
        return None  # Computed from actual data
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "num_samples": self.num_samples,
            "num_classes": self.num_classes,
            "class_names": list(self.class_names),
            "split": self.split,
            "hash": self.hash,
            "path": str(self.path) if self.path else None,
        }
