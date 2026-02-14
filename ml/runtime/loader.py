"""
Model Loader — Singleton Model Management

This module provides lazy-loading and caching of ML models.
Models are loaded once and reused across inference requests.

IMPORTANT: This module should be imported by the ML runtime only,
not directly by Django views.
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Lazy loading and caching of multiple ML models.
    """

    _models = {}

    @classmethod
    def get_model(cls, name, loader_func):
        if name not in cls._models:
            logger.info(f"Loading model: {name}")
            cls._models[name] = loader_func()
        else:
            logger.info(f"Using cached model: {name}")
        return cls._models[name]


from functools import lru_cache


@lru_cache(maxsize=4)
def load_animal_model():
    from tensorflow.keras.models import load_model
    from ml.errors import ModelLoadError

    model_path = Path(__file__).parent.parent / "models_store" / "animal_classifier.h5"
    try:
        return load_model(str(model_path))
    except Exception as e:
        raise ModelLoadError(f"Failed to load animal model: {str(e)}")


class ModelLoaderSingleton:
    """
    Singleton class for loading and caching ML models.

    Features:
    - Lazy initialization (models loaded on first use)
    - Thread-safe singleton pattern
    - Graceful failure handling
    - Reload support for model updates
    """

    _instance: Optional["ModelLoader"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._model: Optional[Any] = None
        self._model_path: Optional[Path] = None
        self._model_name: str = "unknown"
        self._is_loaded: bool = False
        self._load_error: Optional[str] = None
        self._initialized = True

        logger.info("ModelLoader initialized")

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Load a model from the specified path.

        Args:
            model_path: Path to the model file. If None, uses default.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        if model_path is None:
            # Default model path
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_path = base_dir / "assets" / "baseline_mariya.keras"
        else:
            model_path = Path(model_path)

        self._model_path = model_path
        self._model_name = model_path.stem

        if not model_path.exists():
            self._load_error = f"Model file not found: {model_path}"
            logger.error(self._load_error)
            self._is_loaded = False
            return False

        try:
            # Import TensorFlow only when needed
            import tensorflow as tf

            logger.info(f"Loading model from: {model_path}")

            # Check if it's an HDF5 weights-only file
            import h5py

            is_weights_only = False
            try:
                with h5py.File(str(model_path), "r") as f:
                    keys = list(f.keys())
                    # Weights-only files have 'model_weights' but no 'model_config'
                    if "model_weights" in keys and "model_config" not in keys:
                        is_weights_only = True
                        logger.warning(
                            f"File appears to be weights-only (no model config)"
                        )
            except Exception:
                pass

            if is_weights_only:
                # Build the architecture and load weights manually from HDF5
                self._model = self._build_default_model()
                self._load_weights_from_hdf5(str(model_path))
                logger.info("Loaded weights into default architecture")
            else:
                # Try standard loading
                self._model = tf.keras.models.load_model(str(model_path), compile=False)

            self._is_loaded = True
            self._load_error = None
            logger.info(f"Model '{self._model_name}' loaded successfully")
            return True

        except ImportError as e:
            self._load_error = f"TensorFlow not available: {e}"
            logger.error(self._load_error)
            self._is_loaded = False
            return False

        except Exception as e:
            self._load_error = f"Failed to load model: {e}"
            logger.error(self._load_error)
            self._is_loaded = False
            return False

    def _build_default_model(self):
        """
        Build the default CNN architecture matching the saved weights.
        This is used when loading weights-only files.

        Architecture (from baseline_mariya.keras weights):
        - Input: 32x32x3
        - Conv2D: 32 filters, 3x3, same padding, relu
        - MaxPooling2D: 2x2
        - Conv2D: 32 filters, 5x5, same padding, relu
        - MaxPooling2D: 2x2
        - Flatten: -> 2048
        - Dense: 64 units, relu
        - Dense: 10 units, softmax (10-class classifier)
        """
        import tensorflow as tf

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(32, 32, 3)),
                tf.keras.layers.Conv2D(
                    32, (3, 3), activation="relu", padding="same", name="conv2d"
                ),
                tf.keras.layers.MaxPooling2D((2, 2), name="max_pooling2d"),
                tf.keras.layers.Conv2D(
                    32, (5, 5), activation="relu", padding="same", name="conv2d_1"
                ),
                tf.keras.layers.MaxPooling2D((2, 2), name="max_pooling2d_1"),
                tf.keras.layers.Flatten(name="flatten"),
                tf.keras.layers.Dense(64, activation="relu", name="dense"),
                tf.keras.layers.Dense(10, activation="softmax", name="dense_1"),
            ]
        )

        logger.info(
            f"Built default model architecture: input_shape=(32, 32, 3), output_classes=10"
        )
        return model

    def _load_weights_from_hdf5(self, model_path: str) -> None:
        """
        Manually load weights from HDF5 file into model layers.

        This handles the legacy HDF5 weight format that TensorFlow 2.20's
        load_weights() cannot read directly.

        Args:
            model_path: Path to the HDF5 weights file.
        """
        import h5py
        import numpy as np

        with h5py.File(model_path, "r") as f:
            weights_group = f["model_weights"]

            for layer in self._model.layers:
                # Skip layers that don't have learnable weights
                if not layer.weights:
                    continue

                if layer.name not in weights_group:
                    logger.warning(f"Layer {layer.name} not found in weights file")
                    continue

                layer_group = weights_group[layer.name][layer.name]

                # Get kernel and bias in the correct order
                weights = []
                if "kernel:0" in layer_group:
                    weights.append(np.array(layer_group["kernel:0"]))
                if "bias:0" in layer_group:
                    weights.append(np.array(layer_group["bias:0"]))

                if weights:
                    layer.set_weights(weights)
                    logger.debug(
                        f"Loaded weights for {layer.name}: {[w.shape for w in weights]}"
                    )

        logger.info("Successfully loaded all weights from HDF5 file")

    def get_model(self) -> Optional[Any]:
        """
        Get the loaded model, loading it if necessary.

        Returns:
            The loaded model, or None if loading failed.
        """
        if not self._is_loaded:
            self.load_model()
        return self._model

    def reload_model(self, model_path: Optional[str] = None) -> bool:
        """
        Force reload the model.

        Args:
            model_path: Optional new model path.

        Returns:
            True if reload successful, False otherwise.
        """
        self._model = None
        self._is_loaded = False
        return self.load_model(model_path)

    @property
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._is_loaded

    @property
    def model_name(self) -> str:
        """Get the name of the loaded model."""
        return self._model_name

    @property
    def load_error(self) -> Optional[str]:
        """Get the last load error, if any."""
        return self._load_error

    def get_status(self) -> dict:
        """Get the current status of the model loader."""
        return {
            "is_loaded": self._is_loaded,
            "model_name": self._model_name,
            "model_path": str(self._model_path) if self._model_path else None,
            "error": self._load_error,
        }


# Singleton instance
_model_loader = ModelLoader()


def get_model() -> Optional[Any]:
    """
    Convenience function to get the loaded model.

    Returns:
        The loaded model, or None if not available.
    """
    return _model_loader.get_model()


def get_model_loader() -> ModelLoader:
    """
    Get the ModelLoader singleton instance.

    Returns:
        The ModelLoader instance.
    """
    return _model_loader
