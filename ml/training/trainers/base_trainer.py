"""
Base Trainer

Abstract base class for all trainers in the training system.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)

M = TypeVar("M")  # Model type
D = TypeVar("D")  # Dataset type


@dataclass
class TrainerConfig:
    """
    Training configuration.
    
    Attributes:
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Initial learning rate
        optimizer: Optimizer name
        loss: Loss function name
        metrics: List of metrics to track
        early_stopping_patience: Patience for early stopping
        checkpoint_dir: Directory for checkpoints
        seed: Random seed
    """
    
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss: str = "categorical_crossentropy"
    metrics: list[str] = field(default_factory=lambda: ["accuracy"])
    early_stopping_patience: int = 15
    early_stopping_monitor: str = "val_loss"
    early_stopping_mode: str = "min"
    restore_best_weights: bool = True
    lr_reduce_patience: int = 5
    lr_reduce_factor: float = 0.5
    min_lr: float = 1e-6
    checkpoint_dir: Path | None = None
    seed: int = 42
    verbose: int = 1
    
    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "TrainerConfig":
        """Create from dictionary."""
        training = config.get("training", config)
        early_stopping = config.get("early_stopping", {})
        lr_schedule = config.get("lr_schedule", {})
        reproducibility = config.get("reproducibility", {})
        checkpointing = config.get("checkpointing", {})
        
        return cls(
            epochs=training.get("epochs", 100),
            batch_size=training.get("batch_size", 32),
            learning_rate=training.get("initial_learning_rate", 0.001),
            optimizer=training.get("optimizer", "adam"),
            loss=training.get("loss", "categorical_crossentropy"),
            metrics=training.get("metrics", ["accuracy"]),
            early_stopping_patience=early_stopping.get("patience", 15),
            early_stopping_monitor=early_stopping.get("monitor", "val_loss"),
            early_stopping_mode=early_stopping.get("mode", "min"),
            restore_best_weights=early_stopping.get("restore_best_weights", True),
            lr_reduce_patience=lr_schedule.get("patience", 5),
            lr_reduce_factor=lr_schedule.get("factor", 0.5),
            min_lr=lr_schedule.get("min_lr", 1e-6),
            seed=reproducibility.get("seed", 42),
            checkpoint_dir=Path(checkpointing.get("dir", "checkpoints")) if checkpointing.get("enabled") else None,
        )


@dataclass
class TrainingHistory:
    """
    Training history containing metrics per epoch.
    
    Attributes:
        train_loss: Training loss per epoch
        val_loss: Validation loss per epoch
        train_metrics: Training metrics per epoch
        val_metrics: Validation metrics per epoch
        epochs_trained: Number of epochs completed
        best_epoch: Epoch with best validation metric
        best_val_metric: Best validation metric value
        training_time_seconds: Total training time
        early_stopped: Whether training was early stopped
    """
    
    train_loss: list[float] = field(default_factory=list)
    val_loss: list[float] = field(default_factory=list)
    train_metrics: dict[str, list[float]] = field(default_factory=dict)
    val_metrics: dict[str, list[float]] = field(default_factory=dict)
    epochs_trained: int = 0
    best_epoch: int = 0
    best_val_metric: float = 0.0
    training_time_seconds: float = 0.0
    early_stopped: bool = False
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    def add_epoch(
        self,
        train_loss: float,
        val_loss: float,
        train_metrics: dict[str, float],
        val_metrics: dict[str, float],
    ) -> None:
        """Add metrics for one epoch."""
        self.train_loss.append(train_loss)
        self.val_loss.append(val_loss)
        
        for key, value in train_metrics.items():
            if key not in self.train_metrics:
                self.train_metrics[key] = []
            self.train_metrics[key].append(value)
        
        for key, value in val_metrics.items():
            if key not in self.val_metrics:
                self.val_metrics[key] = []
            self.val_metrics[key].append(value)
        
        self.epochs_trained += 1
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "train_loss": self.train_loss,
            "val_loss": self.val_loss,
            "train_metrics": self.train_metrics,
            "val_metrics": self.val_metrics,
            "epochs_trained": self.epochs_trained,
            "best_epoch": self.best_epoch,
            "best_val_metric": self.best_val_metric,
            "training_time_seconds": self.training_time_seconds,
            "early_stopped": self.early_stopped,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @property
    def final_train_loss(self) -> float:
        """Get final training loss."""
        return self.train_loss[-1] if self.train_loss else 0.0
    
    @property
    def final_val_loss(self) -> float:
        """Get final validation loss."""
        return self.val_loss[-1] if self.val_loss else 0.0


class BaseModelTrainer(ABC, Generic[M, D]):
    """
    Abstract base class for model trainers.
    
    Provides common training functionality and enforces
    consistent interface across different frameworks.
    """
    
    def __init__(self, config: TrainerConfig) -> None:
        """
        Initialize trainer.
        
        Args:
            config: Training configuration
        """
        self.config = config
        self._callbacks: list[Callable[[int, dict[str, float]], None]] = []
        self._history: TrainingHistory | None = None
    
    def add_callback(
        self,
        callback: Callable[[int, dict[str, float]], None],
    ) -> None:
        """
        Add a callback to be called after each epoch.
        
        Args:
            callback: Function taking (epoch, metrics) -> None
        """
        self._callbacks.append(callback)
    
    def _run_callbacks(self, epoch: int, metrics: dict[str, float]) -> None:
        """Run all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(epoch, metrics)
            except Exception as e:
                logger.warning(f"Callback error: {e}")
    
    @property
    def history(self) -> TrainingHistory | None:
        """Get training history."""
        return self._history
    
    @abstractmethod
    def train(
        self,
        model: M,
        train_data: D,
        val_data: D | None = None,
    ) -> TrainingHistory:
        """
        Train the model.
        
        Args:
            model: Model to train
            train_data: Training dataset
            val_data: Validation dataset
        
        Returns:
            TrainingHistory with metrics
        """
        ...
    
    @abstractmethod
    def evaluate(
        self,
        model: M,
        test_data: D,
    ) -> dict[str, float]:
        """
        Evaluate model on test data.
        
        Args:
            model: Trained model
            test_data: Test dataset
        
        Returns:
            Dictionary of evaluation metrics
        """
        ...
    
    @abstractmethod
    def save_model(self, model: M, path: Path) -> None:
        """
        Save model to disk.
        
        Args:
            model: Model to save
            path: Save path
        """
        ...
    
    @abstractmethod
    def load_model(self, path: Path) -> M:
        """
        Load model from disk.
        
        Args:
            path: Model path
        
        Returns:
            Loaded model
        """
        ...
