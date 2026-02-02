"""
Metrics Schemas

Defines structured metrics for training and evaluation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray


class MetricType(str, Enum):
    """Types of metrics."""
    
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    AUC_ROC = "auc_roc"
    LOSS = "loss"
    CUSTOM = "custom"


@dataclass(frozen=True)
class MetricValue:
    """
    Single metric value with metadata.
    
    Attributes:
        name: Metric name
        value: Metric value
        metric_type: Type of metric
        higher_is_better: Whether higher values are better
        epoch: Training epoch (if applicable)
        step: Training step (if applicable)
    """
    
    name: str
    value: float
    metric_type: MetricType = MetricType.CUSTOM
    higher_is_better: bool = True
    epoch: int | None = None
    step: int | None = None
    
    def __post_init__(self) -> None:
        """Validate metric value."""
        if np.isnan(self.value) or np.isinf(self.value):
            raise ValueError(f"Invalid metric value: {self.value}")
    
    def is_better_than(self, other: "MetricValue") -> bool:
        """
        Compare with another metric value.
        
        Args:
            other: Metric to compare with
        
        Returns:
            True if this metric is better
        """
        if self.name != other.name:
            raise ValueError(f"Cannot compare different metrics: {self.name} vs {other.name}")
        
        if self.higher_is_better:
            return self.value > other.value
        return self.value < other.value


@dataclass
class ClassificationMetrics:
    """
    Complete classification metrics.
    
    Attributes:
        accuracy: Overall accuracy
        precision_macro: Macro-averaged precision
        recall_macro: Macro-averaged recall
        f1_macro: Macro-averaged F1 score
        precision_per_class: Per-class precision
        recall_per_class: Per-class recall
        f1_per_class: Per-class F1 score
        confusion_matrix: Confusion matrix
        class_names: Class labels
        support: Number of samples per class
    """
    
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    precision_per_class: tuple[float, ...]
    recall_per_class: tuple[float, ...]
    f1_per_class: tuple[float, ...]
    confusion_matrix: NDArray[np.int64] | None = None
    class_names: tuple[str, ...] = ()
    support: tuple[int, ...] = ()
    
    @property
    def num_classes(self) -> int:
        """Number of classes."""
        return len(self.precision_per_class)
    
    def get_per_class_report(self) -> dict[str, dict[str, float]]:
        """
        Get per-class metrics report.
        
        Returns:
            Dictionary mapping class names to their metrics
        """
        report = {}
        names = self.class_names or tuple(f"class_{i}" for i in range(self.num_classes))
        
        for i, name in enumerate(names):
            report[name] = {
                "precision": self.precision_per_class[i],
                "recall": self.recall_per_class[i],
                "f1_score": self.f1_per_class[i],
                "support": self.support[i] if self.support else 0,
            }
        
        return report
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "accuracy": self.accuracy,
            "precision_macro": self.precision_macro,
            "recall_macro": self.recall_macro,
            "f1_macro": self.f1_macro,
            "per_class": self.get_per_class_report(),
            "confusion_matrix": (
                self.confusion_matrix.tolist() 
                if self.confusion_matrix is not None 
                else None
            ),
        }


@dataclass
class TrainingMetrics:
    """
    Metrics from a training run.
    
    Attributes:
        train_loss: Final training loss
        train_accuracy: Final training accuracy
        val_loss: Final validation loss
        val_accuracy: Final validation accuracy
        best_val_accuracy: Best validation accuracy achieved
        best_epoch: Epoch with best validation accuracy
        history: Full training history
        epochs_trained: Number of epochs completed
        early_stopped: Whether training was early stopped
    """
    
    train_loss: float
    train_accuracy: float
    val_loss: float | None = None
    val_accuracy: float | None = None
    best_val_accuracy: float | None = None
    best_epoch: int | None = None
    history: dict[str, list[float]] = field(default_factory=dict)
    epochs_trained: int = 0
    early_stopped: bool = False
    training_time_seconds: float = 0.0
    
    def get_metric_history(self, metric_name: str) -> list[float]:
        """
        Get history for a specific metric.
        
        Args:
            metric_name: Name of metric
        
        Returns:
            List of values per epoch
        """
        return self.history.get(metric_name, [])
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "train_loss": self.train_loss,
            "train_accuracy": self.train_accuracy,
            "val_loss": self.val_loss,
            "val_accuracy": self.val_accuracy,
            "best_val_accuracy": self.best_val_accuracy,
            "best_epoch": self.best_epoch,
            "epochs_trained": self.epochs_trained,
            "early_stopped": self.early_stopped,
            "training_time_seconds": self.training_time_seconds,
            "history": self.history,
        }


@dataclass
class MetricsReport:
    """
    Complete metrics report combining training and evaluation.
    
    Attributes:
        training: Training metrics
        evaluation: Evaluation metrics
        model_name: Model identifier
        model_version: Model version
        dataset_name: Dataset used
        created_at: Report timestamp
    """
    
    training: TrainingMetrics | None = None
    evaluation: ClassificationMetrics | None = None
    model_name: str = ""
    model_version: str = ""
    dataset_name: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "dataset_name": self.dataset_name,
            "created_at": self.created_at.isoformat(),
            "training": self.training.to_dict() if self.training else None,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
        }
