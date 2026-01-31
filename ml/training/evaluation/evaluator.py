"""
Model Evaluator

Comprehensive model evaluation with metrics and visualization.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """
    Evaluation results container.
    
    Attributes:
        accuracy: Overall accuracy
        precision: Per-class precision
        recall: Per-class recall
        f1_score: Per-class F1 scores
        confusion_matrix: Confusion matrix
        classification_report: Full classification report
        class_names: List of class names
        predictions: Model predictions
        true_labels: Ground truth labels
        evaluated_at: Evaluation timestamp
    """
    
    accuracy: float = 0.0
    precision: dict[str, float] = field(default_factory=dict)
    recall: dict[str, float] = field(default_factory=dict)
    f1_score: dict[str, float] = field(default_factory=dict)
    confusion_matrix: NDArray[np.int64] | None = None
    classification_report: str = ""
    class_names: list[str] = field(default_factory=list)
    predictions: NDArray[np.int64] | None = None
    true_labels: NDArray[np.int64] | None = None
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Aggregate metrics
    macro_precision: float = 0.0
    macro_recall: float = 0.0
    macro_f1: float = 0.0
    weighted_precision: float = 0.0
    weighted_recall: float = 0.0
    weighted_f1: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "accuracy": self.accuracy,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
            "weighted_precision": self.weighted_precision,
            "weighted_recall": self.weighted_recall,
            "weighted_f1": self.weighted_f1,
            "per_class": {
                cls: {
                    "precision": self.precision.get(cls, 0.0),
                    "recall": self.recall.get(cls, 0.0),
                    "f1_score": self.f1_score.get(cls, 0.0),
                }
                for cls in self.class_names
            },
            "confusion_matrix": self.confusion_matrix.tolist() if self.confusion_matrix is not None else None,
            "class_names": self.class_names,
            "evaluated_at": self.evaluated_at.isoformat(),
        }
    
    def save(self, path: Path) -> None:
        """Save evaluation results to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Evaluation results saved to {path}")
    
    @classmethod
    def load(cls, path: Path) -> "EvaluationResult":
        """Load evaluation results from JSON."""
        with open(path) as f:
            data = json.load(f)
        
        result = cls(
            accuracy=data["accuracy"],
            macro_precision=data["macro_precision"],
            macro_recall=data["macro_recall"],
            macro_f1=data["macro_f1"],
            weighted_precision=data["weighted_precision"],
            weighted_recall=data["weighted_recall"],
            weighted_f1=data["weighted_f1"],
            class_names=data["class_names"],
        )
        
        # Restore per-class metrics
        for cls_name, metrics in data.get("per_class", {}).items():
            result.precision[cls_name] = metrics["precision"]
            result.recall[cls_name] = metrics["recall"]
            result.f1_score[cls_name] = metrics["f1_score"]
        
        if data.get("confusion_matrix"):
            result.confusion_matrix = np.array(data["confusion_matrix"])
        
        return result


class ModelEvaluator:
    """
    Model evaluator for classification tasks.
    
    Computes comprehensive evaluation metrics:
    - Accuracy
    - Precision, Recall, F1 (per-class and aggregate)
    - Confusion matrix
    - Classification report
    
    Example:
        >>> evaluator = ModelEvaluator(class_names=["Normal", "Tumor"])
        >>> result = evaluator.evaluate(model, test_images, test_labels)
        >>> print(f"Accuracy: {result.accuracy:.2%}")
    """
    
    def __init__(self, class_names: list[str] | None = None) -> None:
        """
        Initialize evaluator.
        
        Args:
            class_names: List of class names
        """
        self.class_names = class_names or []
    
    def evaluate(
        self,
        model: Any,
        images: NDArray[np.float32],
        labels: NDArray[np.int64],
        batch_size: int = 32,
    ) -> EvaluationResult:
        """
        Evaluate model on test data.
        
        Args:
            model: Trained model with predict method
            images: Test images
            labels: True labels
            batch_size: Batch size for prediction
        
        Returns:
            EvaluationResult with all metrics
        """
        logger.info(f"Evaluating on {len(images)} samples")
        
        # Get predictions
        predictions_proba = model.predict(images, batch_size=batch_size, verbose=0)
        predictions = np.argmax(predictions_proba, axis=1)
        
        # Compute metrics
        result = self._compute_metrics(predictions, labels)
        result.predictions = predictions
        result.true_labels = labels
        
        logger.info(f"Evaluation complete. Accuracy: {result.accuracy:.4f}")
        return result
    
    def evaluate_from_predictions(
        self,
        predictions: NDArray[np.int64],
        labels: NDArray[np.int64],
    ) -> EvaluationResult:
        """
        Evaluate from existing predictions.
        
        Args:
            predictions: Model predictions
            labels: True labels
        
        Returns:
            EvaluationResult
        """
        result = self._compute_metrics(predictions, labels)
        result.predictions = predictions
        result.true_labels = labels
        return result
    
    def _compute_metrics(
        self,
        predictions: NDArray[np.int64],
        labels: NDArray[np.int64],
    ) -> EvaluationResult:
        """Compute all evaluation metrics."""
        result = EvaluationResult(class_names=self.class_names)
        
        # Overall accuracy
        result.accuracy = float(np.mean(predictions == labels))
        
        # Confusion matrix
        num_classes = len(self.class_names) if self.class_names else int(max(labels.max(), predictions.max()) + 1)
        cm = np.zeros((num_classes, num_classes), dtype=np.int64)
        for true, pred in zip(labels, predictions):
            cm[true, pred] += 1
        result.confusion_matrix = cm
        
        # Per-class metrics
        class_names = self.class_names or [f"Class_{i}" for i in range(num_classes)]
        
        for i, cls_name in enumerate(class_names):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            result.precision[cls_name] = float(precision)
            result.recall[cls_name] = float(recall)
            result.f1_score[cls_name] = float(f1)
        
        # Macro averages
        result.macro_precision = float(np.mean(list(result.precision.values())))
        result.macro_recall = float(np.mean(list(result.recall.values())))
        result.macro_f1 = float(np.mean(list(result.f1_score.values())))
        
        # Weighted averages
        class_counts = cm.sum(axis=1)
        total = class_counts.sum()
        
        if total > 0:
            weights = class_counts / total
            result.weighted_precision = float(np.sum([
                result.precision[cls] * w
                for cls, w in zip(class_names, weights)
            ]))
            result.weighted_recall = float(np.sum([
                result.recall[cls] * w
                for cls, w in zip(class_names, weights)
            ]))
            result.weighted_f1 = float(np.sum([
                result.f1_score[cls] * w
                for cls, w in zip(class_names, weights)
            ]))
        
        # Classification report string
        result.classification_report = self._format_classification_report(result)
        
        return result
    
    def _format_classification_report(self, result: EvaluationResult) -> str:
        """Format classification report as string."""
        lines = [
            "Classification Report",
            "=" * 60,
            f"{'Class':<20} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}",
            "-" * 60,
        ]
        
        for cls_name in result.class_names:
            lines.append(
                f"{cls_name:<20} "
                f"{result.precision.get(cls_name, 0):.4f}     "
                f"{result.recall.get(cls_name, 0):.4f}     "
                f"{result.f1_score.get(cls_name, 0):.4f}"
            )
        
        lines.extend([
            "-" * 60,
            f"{'Macro Avg':<20} "
            f"{result.macro_precision:.4f}     "
            f"{result.macro_recall:.4f}     "
            f"{result.macro_f1:.4f}",
            f"{'Weighted Avg':<20} "
            f"{result.weighted_precision:.4f}     "
            f"{result.weighted_recall:.4f}     "
            f"{result.weighted_f1:.4f}",
            "=" * 60,
            f"Overall Accuracy: {result.accuracy:.4f}",
        ])
        
        return "\n".join(lines)
    
    def print_report(self, result: EvaluationResult) -> None:
        """Print classification report."""
        print(result.classification_report)
    
    def print_confusion_matrix(self, result: EvaluationResult) -> None:
        """Print confusion matrix."""
        if result.confusion_matrix is None:
            print("No confusion matrix available")
            return
        
        print("\nConfusion Matrix:")
        print("-" * 40)
        
        # Header
        header = "Actual\\Pred  " + "  ".join(f"{cls[:8]:>8}" for cls in result.class_names)
        print(header)
        print("-" * len(header))
        
        # Rows
        for i, cls_name in enumerate(result.class_names):
            row = f"{cls_name[:12]:<12}  " + "  ".join(
                f"{result.confusion_matrix[i, j]:>8d}"
                for j in range(len(result.class_names))
            )
            print(row)
