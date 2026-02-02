"""
Reproducibility Utilities

Ensures reproducible training and inference through:
- Fixed random seeds
- Deterministic operations
- Hash-based versioning
- Configuration snapshots
"""

import hashlib
import json
import os
import random
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


def set_seed(seed: int = 42, deterministic: bool = True) -> None:
    """
    Set random seeds for reproducibility.
    
    Sets seeds for Python random, NumPy, and optionally enables
    deterministic operations for deep learning frameworks.
    
    Args:
        seed: Random seed value
        deterministic: Whether to enable deterministic operations
    
    Example:
        >>> set_seed(42)
        >>> np.random.rand(3)  # Reproducible
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # TensorFlow (if available)
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        
        if deterministic:
            # Enable deterministic operations
            os.environ["TF_DETERMINISTIC_OPS"] = "1"
            os.environ["TF_CUDNN_DETERMINISTIC"] = "1"
    except ImportError:
        pass
    
    # PyTorch (if available)
    try:
        import torch
        torch.manual_seed(seed)
        
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def get_deterministic_config() -> dict[str, Any]:
    """
    Get configuration for deterministic execution.
    
    Returns:
        Dictionary of environment settings for reproducibility
    """
    return {
        "TF_DETERMINISTIC_OPS": "1",
        "TF_CUDNN_DETERMINISTIC": "1",
        "PYTHONHASHSEED": "42",
        "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
    }


def compute_hash(
    data: bytes | str | Path | dict[str, Any],
    algorithm: str = "sha256",
) -> str:
    """
    Compute hash of data for versioning.
    
    Supports bytes, strings, file paths, and dictionaries.
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (sha256, md5, etc.)
    
    Returns:
        Hex digest of hash
    
    Example:
        >>> compute_hash({"learning_rate": 0.001})
        'a1b2c3...'
        >>> compute_hash(Path("data/train.csv"))
        'd4e5f6...'
    """
    hasher = hashlib.new(algorithm)
    
    if isinstance(data, bytes):
        hasher.update(data)
    
    elif isinstance(data, str):
        hasher.update(data.encode("utf-8"))
    
    elif isinstance(data, Path):
        if data.is_file():
            with open(data, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        elif data.is_dir():
            for file_path in sorted(data.rglob("*")):
                if file_path.is_file():
                    hasher.update(str(file_path.relative_to(data)).encode())
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            hasher.update(chunk)
        else:
            raise FileNotFoundError(f"Path not found: {data}")
    
    elif isinstance(data, dict):
        # Sort keys for deterministic hashing
        json_str = json.dumps(data, sort_keys=True, default=str)
        hasher.update(json_str.encode("utf-8"))
    
    else:
        raise TypeError(f"Unsupported type for hashing: {type(data)}")
    
    return hasher.hexdigest()


def snapshot_config(
    config: dict[str, Any] | Any,
    output_path: Path,
    include_environment: bool = True,
) -> Path:
    """
    Save a configuration snapshot for reproducibility.
    
    Captures all configuration values and optionally environment info.
    
    Args:
        config: Configuration to snapshot (dict or dataclass)
        output_path: Path to save snapshot
        include_environment: Include environment variables
    
    Returns:
        Path to saved snapshot
    
    Example:
        >>> config = TrainingConfig(epochs=100, lr=0.001)
        >>> snapshot_config(config, Path("experiments/run_001/config.json"))
    """
    # Convert dataclass to dict if needed
    if is_dataclass(config) and not isinstance(config, dict):
        config_dict = asdict(config)
    elif isinstance(config, dict):
        config_dict = config.copy()
    else:
        config_dict = {"value": config}
    
    snapshot = {
        "config": config_dict,
        "timestamp": datetime.utcnow().isoformat(),
        "config_hash": compute_hash(config_dict),
    }
    
    if include_environment:
        snapshot["environment"] = {
            "python_version": _get_python_version(),
            "numpy_version": np.__version__,
            "platform": _get_platform_info(),
            "packages": _get_ml_package_versions(),
        }
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)
    
    return output_path


def _get_python_version() -> str:
    """Get Python version string."""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _get_platform_info() -> dict[str, str]:
    """Get platform information."""
    import platform
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def _get_ml_package_versions() -> dict[str, str]:
    """Get versions of common ML packages."""
    versions = {}
    
    packages = [
        "tensorflow",
        "torch",
        "keras",
        "sklearn",
        "scipy",
        "pandas",
        "pillow",
        "opencv-python",
    ]
    
    for package in packages:
        try:
            module = __import__(package.replace("-", "_"))
            versions[package] = getattr(module, "__version__", "unknown")
        except ImportError:
            pass
    
    return versions


class ReproducibilityContext:
    """
    Context manager for reproducible code blocks.
    
    Example:
        >>> with ReproducibilityContext(seed=42):
        ...     model = train_model(data)
    """
    
    def __init__(
        self,
        seed: int = 42,
        deterministic: bool = True,
        snapshot_path: Path | None = None,
    ) -> None:
        """
        Initialize reproducibility context.
        
        Args:
            seed: Random seed
            deterministic: Enable deterministic ops
            snapshot_path: Optional path to save config snapshot
        """
        self.seed = seed
        self.deterministic = deterministic
        self.snapshot_path = snapshot_path
        self._original_env: dict[str, str | None] = {}
    
    def __enter__(self) -> "ReproducibilityContext":
        """Enter context and set seeds."""
        # Save original environment
        det_config = get_deterministic_config()
        for key in det_config:
            self._original_env[key] = os.environ.get(key)
        
        # Set seeds and deterministic config
        set_seed(self.seed, self.deterministic)
        
        if self.deterministic:
            for key, value in det_config.items():
                os.environ[key] = value
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore environment."""
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
