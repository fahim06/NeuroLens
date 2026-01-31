"""
Trainer Interface Contract

Defines the abstract base class for model training.
Enforces consistent training interface with reproducibility support.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray


# Type aliases
MetricsDict = dict[str, float]
CallbackFn = Callable[[int, MetricsDict], None]
M = TypeVar("M")  # Model type


@dataclass
class TrainingConfig:
    """
    Configuration for model training.
    
    Attributes:
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Initial learning rate
        optimizer: Optimizer name (adam, sgd, etc.)
        loss: Loss function name
        early_stopping_patience: Epochs to wait before stopping
        checkpoint_dir: Directory for checkpoints
        seed: Random seed for reproducibility
        extra: Additional framework-specific config
    """
    
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-4
    optimizer: str = "adam"
    loss: str = "categorical_crossentropy"
    early_stopping_patience: int = 10
    checkpoint_dir: Path | None = None
    seed: int = 42
    extra: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "optimizer": self.optimizer,
            "loss": self.loss,
            "early_stopping_patience": self.early_stopping_patience,
            "checkpoint_dir": str(self.checkpoint_dir) if self.checkpoint_dir else None,
            "seed": self.seed,
            "extra": self.extra,
        }


@dataclass
class TrainingResult:
    """
    Result of a training run.
    
    Attributes:
        final_metrics: Final training/validation metrics
        best_metrics: Best metrics achieved during training
        history: Per-epoch metrics history
        epochs_trained: Actual number of epochs trained
        training_time_seconds: Total training time
        model_path: Path to saved model
        config: Training configuration used
    """
    
    final_metrics: MetricsDict
    best_metrics: MetricsDict
    history: dict[str, list[float]]
    epochs_trained: int
    training_time_seconds: float
    model_path: Path | None = None
    config: TrainingConfig | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)


class BaseTrainer(ABC, Generic[M]):
    """
    Abstract base class for model trainers.
    
    Type Parameters:
        M: Model type being trained
    
    Example:
        >>> trainer = CNNTrainer(model, config)
        >>> result = trainer.train(train_data, val_data)
        >>> print(f"Best accuracy: {result.best_metrics['accuracy']}")
    """
    
    def __init__(
        self,
        model: M,
        config: TrainingConfig | None = None,
    ) -> None:
        """
        Initialize trainer.
        
        Args:
            model: Model to train
            config: Training configuration
        """
        self.model = model
        self.config = config or TrainingConfig()
        self._callbacks: list[CallbackFn] = []
    
    def add_callback(self, callback: CallbackFn) -> None:
        """
        Add a callback to be called after each epoch.
        
        Args:
            callback: Function taking (epoch, metrics) -> None
        """
        self._callbacks.append(callback)
    
    def _run_callbacks(self, epoch: int, metrics: MetricsDict) -> None:
        """Run all registered callbacks."""
        for callback in self._callbacks:
            callback(epoch, metrics)
    
    @abstractmethod
    def train(
        self,
        train_data: Any,
        val_data: Any | None = None,
    ) -> TrainingResult:
        """
        Train the model.
        
        Args:
            train_data: Training dataset
            val_data: Validation dataset (optional)
        
        Returns:
            TrainingResult with metrics and history
        """
        ...
    
    @abstractmethod
    def resume(
        self,
        checkpoint_path: Path,
        train_data: Any,
        val_data: Any | None = None,
    ) -> TrainingResult:
        """
        Resume training from a checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
            train_data: Training dataset
            val_data: Validation dataset
        
        Returns:
            TrainingResult with metrics and history
        """
        ...
    
    @abstractmethod
    def export(self, path: Path, format: str = "native") -> Path:
        """
        Export trained model to specified format.
        
        Args:
            path: Export destination path
            format: Export format (native, onnx, tflite, etc.)
        
        Returns:
            Path to exported model
        """
        ...
    
    def save_checkpoint(
        self,
        path: Path,
        epoch: int,
        metrics: MetricsDict,
    ) -> None:
        """
        Save training checkpoint.
        
        Args:
            path: Checkpoint file path
            epoch: Current epoch number
            metrics: Current metrics
        """
        checkpoint = {
            "epoch": epoch,
            "metrics": metrics,
            "config": self.config.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, checkpoint, allow_pickle=True)
