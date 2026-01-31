"""
Evaluator Interface Contract

Defines the abstract base class for model evaluation.
Supports pluggable metrics and comprehensive evaluation reports.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray


# Type aliases
MetricsDict = dict[str, float]
ConfusionMatrix = NDArray[np.int64]
M = TypeVar("M")  # Model type


@dataclass
class EvaluationResult:
    """
    Comprehensive evaluation result.
    
    Attributes:
        metrics: Computed metrics dictionary
        confusion_matrix: Confusion matrix (optional)
        per_class_metrics: Per-class precision/recall/f1
        predictions: Raw predictions (optional)
        ground_truth: Ground truth labels (optional)
        evaluated_at: Evaluation timestamp
        dataset_info: Information about evaluated dataset
    """
    
    metrics: MetricsDict
    confusion_matrix: ConfusionMatrix | None = None
    per_class_metrics: dict[str, MetricsDict] | None = None
    predictions: NDArray[np.float32] | None = None
    ground_truth: NDArray[np.int64] | None = None
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    dataset_info: dict[str, Any] = field(default_factory=dict)
    
    @property
    def accuracy(self) -> float:
        """Shortcut to accuracy metric."""
        return self.metrics.get("accuracy", 0.0)
    
    @property
    def f1_score(self) -> float:
        """Shortcut to F1 score metric."""
        return self.metrics.get("f1_score", 0.0)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metrics": self.metrics,
            "confusion_matrix": self.confusion_matrix.tolist() if self.confusion_matrix is not None else None,
            "per_class_metrics": self.per_class_metrics,
            "evaluated_at": self.evaluated_at.isoformat(),
            "dataset_info": self.dataset_info,
        }


class BaseEvaluator(ABC, Generic[M]):
    """
    Abstract base class for model evaluators.
    
    Provides pluggable metrics and comprehensive evaluation.
    
    Type Parameters:
        M: Model type being evaluated
    
    Example:
        >>> evaluator = ClassificationEvaluator(metrics=["accuracy", "f1"])
        >>> result = evaluator.evaluate(model, test_data)
        >>> print(f"Accuracy: {result.accuracy:.4f}")
    """
    
    # Standard metrics available
    AVAILABLE_METRICS = frozenset([
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "auc_roc",
        "confusion_matrix",
        "calibration_error",
    ])
    
    def __init__(
        self,
        metrics: list[str] | None = None,
        class_names: list[str] | None = None,
    ) -> None:
        """
        Initialize evaluator.
        
        Args:
            metrics: List of metrics to compute, defaults to all
            class_names: Optional class names for reporting
        """
        self.metrics = metrics or ["accuracy", "precision", "recall", "f1_score"]
        self.class_names = class_names
        
        # Validate metrics
        invalid = set(self.metrics) - self.AVAILABLE_METRICS
        if invalid:
            raise ValueError(f"Unknown metrics: {invalid}")
    
    @abstractmethod
    def evaluate(
        self,
        model: M,
        test_data: Any,
    ) -> EvaluationResult:
        """
        Evaluate model on test data.
        
        Args:
            model: Model to evaluate
            test_data: Test dataset
        
        Returns:
            EvaluationResult with all computed metrics
        """
        ...
    
    @staticmethod
    def compute_accuracy(
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
    ) -> float:
        """
        Compute accuracy score.
        
        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
        
        Returns:
            Accuracy as float in [0, 1]
        """
        return float(np.mean(y_true == y_pred))
    
    @staticmethod
    def compute_precision_recall_f1(
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
        num_classes: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """
        Compute per-class precision, recall, and F1.
        
        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            num_classes: Number of classes
        
        Returns:
            Tuple of (precision, recall, f1) arrays
        """
        precision = np.zeros(num_classes)
        recall = np.zeros(num_classes)
        f1 = np.zeros(num_classes)
        
        for c in range(num_classes):
            true_positives = np.sum((y_pred == c) & (y_true == c))
            false_positives = np.sum((y_pred == c) & (y_true != c))
            false_negatives = np.sum((y_pred != c) & (y_true == c))
            
            if true_positives + false_positives > 0:
                precision[c] = true_positives / (true_positives + false_positives)
            
            if true_positives + false_negatives > 0:
                recall[c] = true_positives / (true_positives + false_negatives)
            
            if precision[c] + recall[c] > 0:
                f1[c] = 2 * (precision[c] * recall[c]) / (precision[c] + recall[c])
        
        return precision, recall, f1
    
    @staticmethod
    def compute_confusion_matrix(
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
        num_classes: int,
    ) -> ConfusionMatrix:
        """
        Compute confusion matrix.
        
        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            num_classes: Number of classes
        
        Returns:
            Confusion matrix of shape [num_classes, num_classes]
        """
        matrix = np.zeros((num_classes, num_classes), dtype=np.int64)
        for true, pred in zip(y_true, y_pred):
            matrix[true, pred] += 1
        return matrix
