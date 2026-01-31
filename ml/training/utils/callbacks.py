"""
Training Callbacks

Custom Keras callbacks for training.
"""

import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None
    keras = None

try:
    import mlflow
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False
    mlflow = None


class MLflowCallback(keras.callbacks.Callback if HAS_TF else object):
    """
    Keras callback for MLflow logging.
    
    Logs metrics at the end of each epoch to MLflow.
    
    Example:
        >>> callback = MLflowCallback()
        >>> model.fit(x, y, callbacks=[callback])
    """
    
    def __init__(self, log_every_n_epochs: int = 1) -> None:
        """
        Initialize callback.
        
        Args:
            log_every_n_epochs: Log every N epochs
        """
        if HAS_TF:
            super().__init__()
        
        self.log_every_n_epochs = log_every_n_epochs
    
    def on_epoch_end(self, epoch: int, logs: dict[str, float] | None = None) -> None:
        """Log metrics at end of epoch."""
        if not HAS_MLFLOW or logs is None:
            return
        
        if (epoch + 1) % self.log_every_n_epochs != 0:
            return
        
        try:
            mlflow.log_metrics(logs, step=epoch + 1)
        except Exception as e:
            logger.warning(f"Failed to log metrics to MLflow: {e}")


class ProgressCallback(keras.callbacks.Callback if HAS_TF else object):
    """
    Keras callback for progress reporting.
    
    Reports training progress with custom formatting.
    """
    
    def __init__(
        self,
        total_epochs: int,
        metrics_to_show: list[str] | None = None,
    ) -> None:
        """
        Initialize callback.
        
        Args:
            total_epochs: Total number of epochs
            metrics_to_show: List of metrics to display
        """
        if HAS_TF:
            super().__init__()
        
        self.total_epochs = total_epochs
        self.metrics_to_show = metrics_to_show or ["loss", "accuracy", "val_loss", "val_accuracy"]
    
    def on_epoch_end(self, epoch: int, logs: dict[str, float] | None = None) -> None:
        """Report progress at end of epoch."""
        if logs is None:
            return
        
        progress = (epoch + 1) / self.total_epochs * 100
        
        metrics_str = " | ".join(
            f"{k}: {v:.4f}"
            for k, v in logs.items()
            if k in self.metrics_to_show
        )
        
        logger.info(f"Epoch {epoch + 1}/{self.total_epochs} ({progress:.1f}%) - {metrics_str}")


class TimingCallback(keras.callbacks.Callback if HAS_TF else object):
    """
    Callback to track epoch timing.
    """
    
    def __init__(self) -> None:
        """Initialize callback."""
        if HAS_TF:
            super().__init__()
        
        self.epoch_times: list[float] = []
        self._epoch_start_time: float = 0.0
    
    def on_epoch_begin(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
        """Record epoch start time."""
        import time
        self._epoch_start_time = time.time()
    
    def on_epoch_end(self, epoch: int, logs: dict[str, Any] | None = None) -> None:
        """Record epoch duration."""
        import time
        epoch_time = time.time() - self._epoch_start_time
        self.epoch_times.append(epoch_time)
        
        if logs is not None:
            logs["epoch_time"] = epoch_time
    
    @property
    def total_time(self) -> float:
        """Total training time."""
        return sum(self.epoch_times)
    
    @property
    def average_epoch_time(self) -> float:
        """Average epoch time."""
        return sum(self.epoch_times) / len(self.epoch_times) if self.epoch_times else 0.0


def create_callbacks(
    config: dict[str, Any],
    checkpoint_dir: Path | None = None,
    use_mlflow: bool = True,
) -> list[keras.callbacks.Callback]:
    """
    Create training callbacks from config.
    
    Args:
        config: Training configuration dictionary
        checkpoint_dir: Directory for checkpoints
        use_mlflow: Whether to use MLflow callback
    
    Returns:
        List of Keras callbacks
    """
    if not HAS_TF:
        return []
    
    callbacks = []
    
    # Early stopping
    early_stopping = config.get("early_stopping", {})
    if early_stopping.get("enabled", True):
        callbacks.append(keras.callbacks.EarlyStopping(
            monitor=early_stopping.get("monitor", "val_loss"),
            patience=early_stopping.get("patience", 15),
            mode=early_stopping.get("mode", "min"),
            restore_best_weights=early_stopping.get("restore_best_weights", True),
            verbose=1,
        ))
    
    # Learning rate reduction
    lr_schedule = config.get("lr_schedule", {})
    if lr_schedule.get("enabled", True):
        callbacks.append(keras.callbacks.ReduceLROnPlateau(
            monitor=lr_schedule.get("monitor", "val_loss"),
            factor=lr_schedule.get("factor", 0.5),
            patience=lr_schedule.get("patience", 5),
            min_lr=lr_schedule.get("min_lr", 1e-6),
            verbose=1,
        ))
    
    # Model checkpointing
    checkpointing = config.get("checkpointing", {})
    if checkpointing.get("enabled", False) and checkpoint_dir:
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / "model_{epoch:03d}.keras"
        callbacks.append(keras.callbacks.ModelCheckpoint(
            str(checkpoint_path),
            save_best_only=checkpointing.get("save_best_only", True),
            monitor=checkpointing.get("monitor", "val_loss"),
            mode=checkpointing.get("mode", "min"),
            verbose=1,
        ))
    
    # TensorBoard
    tensorboard = config.get("tensorboard", {})
    if tensorboard.get("enabled", False):
        log_dir = Path(tensorboard.get("log_dir", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        callbacks.append(keras.callbacks.TensorBoard(
            log_dir=str(log_dir),
            histogram_freq=tensorboard.get("histogram_freq", 0),
            write_graph=tensorboard.get("write_graph", True),
            update_freq=tensorboard.get("update_freq", "epoch"),
        ))
    
    # MLflow callback
    if use_mlflow and HAS_MLFLOW:
        callbacks.append(MLflowCallback())
    
    # Timing callback
    callbacks.append(TimingCallback())
    
    return callbacks
