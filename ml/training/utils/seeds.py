"""
Seed Utilities

Reproducibility utilities for setting random seeds.
"""

import logging
import os
import random
from typing import Any


logger = logging.getLogger(__name__)


def set_seeds(seed: int = 42) -> None:
    """
    Set all random seeds for reproducibility.
    
    Sets seeds for:
    - Python random
    - NumPy
    - TensorFlow
    - PYTHONHASHSEED environment variable
    
    Args:
        seed: Random seed value
    """
    # Python random
    random.seed(seed)
    
    # Environment variable
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # NumPy
    try:
        import numpy as np
        np.random.seed(seed)
        logger.debug(f"NumPy seed set to {seed}")
    except ImportError:
        pass
    
    # TensorFlow
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        
        # Additional TensorFlow reproducibility settings
        os.environ["TF_DETERMINISTIC_OPS"] = "1"
        os.environ["TF_CUDNN_DETERMINISTIC"] = "1"
        
        logger.debug(f"TensorFlow seed set to {seed}")
    except ImportError:
        pass
    
    logger.info(f"All random seeds set to {seed}")


def get_reproducibility_info() -> dict[str, Any]:
    """
    Get reproducibility information.
    
    Returns:
        Dictionary with package versions and settings
    """
    info = {
        "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
        "tf_deterministic_ops": os.environ.get("TF_DETERMINISTIC_OPS"),
    }
    
    # Python version
    import sys
    info["python_version"] = sys.version
    
    # NumPy version
    try:
        import numpy as np
        info["numpy_version"] = np.__version__
    except ImportError:
        info["numpy_version"] = None
    
    # TensorFlow version
    try:
        import tensorflow as tf
        info["tensorflow_version"] = tf.__version__
        
        # GPU info
        gpus = tf.config.list_physical_devices("GPU")
        info["gpu_available"] = len(gpus) > 0
        info["gpu_count"] = len(gpus)
        if gpus:
            info["gpu_names"] = [gpu.name for gpu in gpus]
    except ImportError:
        info["tensorflow_version"] = None
        info["gpu_available"] = False
    
    # MLflow version
    try:
        import mlflow
        info["mlflow_version"] = mlflow.__version__
    except ImportError:
        info["mlflow_version"] = None
    
    return info


def configure_gpu_memory_growth() -> None:
    """
    Configure GPU memory growth to avoid allocating all memory.
    
    Should be called before any TensorFlow operations.
    """
    try:
        import tensorflow as tf
        
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            logger.info(f"GPU memory growth enabled for {len(gpus)} GPU(s)")
    except RuntimeError as e:
        logger.warning(f"GPU memory growth must be set before GPUs are initialized: {e}")
    except ImportError:
        pass


def enable_mixed_precision() -> None:
    """
    Enable mixed precision training for faster computation.
    
    Uses float16 for computations and float32 for variables.
    """
    try:
        import tensorflow as tf
        from tensorflow.keras import mixed_precision
        
        # Set mixed precision policy
        policy = mixed_precision.Policy("mixed_float16")
        mixed_precision.set_global_policy(policy)
        
        logger.info(f"Mixed precision enabled: {policy.name}")
        logger.info(f"Compute dtype: {policy.compute_dtype}")
        logger.info(f"Variable dtype: {policy.variable_dtype}")
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Could not enable mixed precision: {e}")
