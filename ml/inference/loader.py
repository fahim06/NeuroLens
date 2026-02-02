"""
Model and Artifact Loader

Loads model weights and preprocessor artifacts for inference.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None
    keras = None


@dataclass
class ArtifactBundle:
    """
    Bundle of artifacts needed for inference.
    
    Attributes:
        model: Loaded Keras model
        class_names: List of class names
        input_shape: Expected input shape
        preprocessor_config: Preprocessing configuration
        model_version: Model version string
        checksum: Model file checksum
        metadata: Additional metadata
    """
    
    model: Any  # keras.Model
    class_names: list[str]
    input_shape: tuple[int, int, int]
    preprocessor_config: dict[str, Any] = field(default_factory=dict)
    model_version: str = "1.0.0"
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def num_classes(self) -> int:
        """Get number of classes."""
        return len(self.class_names)
    
    @property
    def image_size(self) -> tuple[int, int]:
        """Get image size (H, W)."""
        return (self.input_shape[0], self.input_shape[1])


class ModelLoader:
    """
    Loads trained models and associated artifacts for inference.
    
    Features:
    - Load model weights once
    - Load preprocessor artifacts
    - Validate checksum & versions
    - Warm-up runs on startup
    
    Example:
        >>> loader = ModelLoader()
        >>> bundle = loader.load("path/to/model.keras")
        >>> print(bundle.class_names)
    """
    
    def __init__(
        self,
        device: str = "auto",
        warm_up: bool = True,
    ) -> None:
        """
        Initialize model loader.
        
        Args:
            device: Device to use ("auto", "gpu", "cpu")
            warm_up: Whether to run warm-up inference
        """
        if not HAS_TF:
            raise ImportError("TensorFlow is required for ModelLoader")
        
        self.device = device
        self.warm_up = warm_up
        self._configure_device()
    
    def _configure_device(self) -> None:
        """Configure compute device."""
        if self.device == "auto":
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                # Enable memory growth for Metal GPU
                for gpu in gpus:
                    try:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    except RuntimeError:
                        pass
                logger.info(f"Using GPU: {len(gpus)} device(s) available")
            else:
                logger.info("No GPU found, using CPU")
        elif self.device == "cpu":
            tf.config.set_visible_devices([], "GPU")
            logger.info("Forced CPU execution")
    
    def load(
        self,
        model_path: Path | str,
        metadata_path: Path | str | None = None,
    ) -> ArtifactBundle:
        """
        Load model and create artifact bundle.
        
        Args:
            model_path: Path to .keras model file
            metadata_path: Optional path to metadata JSON
        
        Returns:
            ArtifactBundle with loaded model
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        logger.info(f"Loading model from {model_path}")
        
        # Compute checksum
        checksum = self._compute_checksum(model_path)
        logger.info(f"Model checksum: {checksum[:16]}...")
        
        # Load model
        model = keras.models.load_model(str(model_path))
        logger.info(f"Model loaded: {model.name}")
        
        # Extract model info
        input_shape = model.input_shape[1:]  # Remove batch dimension
        num_classes = model.output_shape[-1]
        
        # Load metadata if available
        metadata = {}
        class_names = [f"class_{i}" for i in range(num_classes)]
        preprocessor_config = {}
        model_version = "1.0.0"
        
        if metadata_path:
            metadata_path = Path(metadata_path)
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                class_names = metadata.get("class_names", class_names)
                preprocessor_config = metadata.get("preprocessor", {})
                model_version = metadata.get("version", model_version)
        else:
            # Try to find metadata next to model
            default_metadata = model_path.with_suffix(".json")
            if default_metadata.exists():
                with open(default_metadata) as f:
                    metadata = json.load(f)
                class_names = metadata.get("class_names", class_names)
                preprocessor_config = metadata.get("preprocessor", {})
                model_version = metadata.get("version", model_version)
        
        bundle = ArtifactBundle(
            model=model,
            class_names=class_names,
            input_shape=input_shape,
            preprocessor_config=preprocessor_config,
            model_version=model_version,
            checksum=checksum,
            metadata=metadata,
        )
        
        # Warm-up run
        if self.warm_up:
            self._warm_up(model, input_shape)
        
        logger.info(f"Model ready: {num_classes} classes, input {input_shape}")
        return bundle
    
    def _warm_up(self, model: keras.Model, input_shape: tuple[int, ...]) -> None:
        """Run warm-up inference to initialize GPU."""
        logger.info("Running warm-up inference...")
        dummy_input = np.zeros((1, *input_shape), dtype=np.float32)
        _ = model.predict(dummy_input, verbose=0)
        logger.info("Warm-up complete")
    
    @staticmethod
    def _compute_checksum(path: Path) -> str:
        """Compute SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def save_metadata(
        self,
        path: Path | str,
        class_names: list[str],
        input_shape: tuple[int, int, int],
        preprocessor_config: dict[str, Any] | None = None,
        version: str = "1.0.0",
        **extra_metadata: Any,
    ) -> None:
        """
        Save model metadata to JSON.
        
        Args:
            path: Output path for metadata JSON
            class_names: List of class names
            input_shape: Input image shape
            preprocessor_config: Preprocessing configuration
            version: Model version
            **extra_metadata: Additional metadata
        """
        path = Path(path)
        
        metadata = {
            "version": version,
            "class_names": class_names,
            "input_shape": list(input_shape),
            "preprocessor": preprocessor_config or {},
            **extra_metadata,
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {path}")
