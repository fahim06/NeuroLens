"""
Evaluation Pipeline

Comprehensive model evaluation with pluggable metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

from ml.core.interfaces.model import BaseModel
from ml.core.interfaces.evaluator import BaseEvaluator, EvaluationResult
from ml.core.schemas.metrics import ClassificationMetrics, MetricsReport
from ml.pipelines.preprocess import PreprocessingPipeline


M = TypeVar("M", bound=BaseModel)


@dataclass
class EvaluationPipelineConfig:
    """
    Configuration for evaluation pipeline.
    
    Attributes:
        metrics: List of metrics to compute
        compute_confusion_matrix: Whether to compute confusion matrix
        compute_per_class: Whether to compute per-class metrics
        save_predictions: Whether to save raw predictions
        output_dir: Directory for evaluation outputs
    """
    
    metrics: list[str] = field(
        default_factory=lambda: ["accuracy", "precision", "recall", "f1_score"]
    )
    compute_confusion_matrix: bool = True
    compute_per_class: bool = True
    save_predictions: bool = False
    output_dir: Path | None = None


@dataclass
class EvaluationPipelineResult:
    """
    Complete evaluation result.
    
    Attributes:
        classification_metrics: Computed classification metrics
        evaluation_result: Raw evaluation result
        model_name: Evaluated model name
        model_version: Evaluated model version
        dataset_info: Information about test dataset
        evaluated_at: Evaluation timestamp
    """
    
    classification_metrics: ClassificationMetrics
    evaluation_result: EvaluationResult
    model_name: str = ""
    model_version: str = ""
    dataset_info: dict[str, Any] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_report(self) -> MetricsReport:
        """Convert to metrics report."""
        return MetricsReport(
            evaluation=self.classification_metrics,
            model_name=self.model_name,
            model_version=self.model_version,
            dataset_name=self.dataset_info.get("name", ""),
            created_at=self.evaluated_at,
        )


class EvaluationPipeline(Generic[M]):
    """
    Complete evaluation pipeline.
    
    Handles preprocessing, prediction, and metrics computation.
    
    Example:
        >>> pipeline = EvaluationPipeline(model, config)
        >>> result = pipeline.evaluate(test_images, test_labels)
    """
    
    def __init__(
        self,
        model: M,
        preprocessor: PreprocessingPipeline | None = None,
        config: EvaluationPipelineConfig | None = None,
    ) -> None:
        """
        Initialize evaluation pipeline.
        
        Args:
            model: Model to evaluate
            preprocessor: Optional preprocessing pipeline
            config: Evaluation configuration
        """
        self.model = model
        self.preprocessor = preprocessor
        self.config = config or EvaluationPipelineConfig()
    
    def evaluate(
        self,
        images: NDArray[np.float32],
        labels: NDArray[np.int64],
        class_names: list[str] | None = None,
    ) -> EvaluationPipelineResult:
        """
        Evaluate model on test data.
        
        Args:
            images: Test images [N, H, W, C]
            labels: Ground truth labels [N]
            class_names: Optional class names
        
        Returns:
            EvaluationPipelineResult with all metrics
        """
        # Preprocess if pipeline provided
        if self.preprocessor is not None:
            images = self.preprocessor.transform(images)
        
        # Get predictions
        probabilities = self.model.predict(images)
        predictions = np.argmax(probabilities, axis=-1)
        
        # Use model's class names if not provided
        if class_names is None:
            class_names = list(self.model.output_classes)
        
        num_classes = len(class_names)
        
        # Compute metrics
        accuracy = self._compute_accuracy(labels, predictions)
        precision, recall, f1 = self._compute_prf(
            labels, predictions, num_classes
        )
        
        confusion_matrix = None
        if self.config.compute_confusion_matrix:
            confusion_matrix = self._compute_confusion_matrix(
                labels, predictions, num_classes
            )
        
        # Compute support (samples per class)
        support = tuple(
            int(np.sum(labels == i)) for i in range(num_classes)
        )
        
        # Create classification metrics
        classification_metrics = ClassificationMetrics(
            accuracy=accuracy,
            precision_macro=float(np.mean(precision)),
            recall_macro=float(np.mean(recall)),
            f1_macro=float(np.mean(f1)),
            precision_per_class=tuple(precision.tolist()),
            recall_per_class=tuple(recall.tolist()),
            f1_per_class=tuple(f1.tolist()),
            confusion_matrix=confusion_matrix,
            class_names=tuple(class_names),
            support=support,
        )
        
        # Create evaluation result
        evaluation_result = EvaluationResult(
            metrics={
                "accuracy": accuracy,
                "precision": float(np.mean(precision)),
                "recall": float(np.mean(recall)),
                "f1_score": float(np.mean(f1)),
            },
            confusion_matrix=confusion_matrix,
            per_class_metrics=(
                classification_metrics.get_per_class_report()
                if self.config.compute_per_class
                else None
            ),
            predictions=probabilities if self.config.save_predictions else None,
            ground_truth=labels if self.config.save_predictions else None,
        )
        
        result = EvaluationPipelineResult(
            classification_metrics=classification_metrics,
            evaluation_result=evaluation_result,
            model_name=self.model.name,
            model_version=self.model.version,
            dataset_info={
                "num_samples": len(labels),
                "num_classes": num_classes,
                "class_distribution": dict(zip(class_names, support)),
            },
        )
        
        # Save if configured
        if self.config.output_dir is not None:
            self._save_results(result)
        
        return result
    
    def _compute_accuracy(
        self,
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
    ) -> float:
        """Compute accuracy."""
        return float(np.mean(y_true == y_pred))
    
    def _compute_prf(
        self,
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
        num_classes: int,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Compute precision, recall, F1 per class."""
        precision = np.zeros(num_classes)
        recall = np.zeros(num_classes)
        f1 = np.zeros(num_classes)
        
        for c in range(num_classes):
            tp = np.sum((y_pred == c) & (y_true == c))
            fp = np.sum((y_pred == c) & (y_true != c))
            fn = np.sum((y_pred != c) & (y_true == c))
            
            if tp + fp > 0:
                precision[c] = tp / (tp + fp)
            
            if tp + fn > 0:
                recall[c] = tp / (tp + fn)
            
            if precision[c] + recall[c] > 0:
                f1[c] = 2 * precision[c] * recall[c] / (precision[c] + recall[c])
        
        return precision, recall, f1
    
    def _compute_confusion_matrix(
        self,
        y_true: NDArray[np.int64],
        y_pred: NDArray[np.int64],
        num_classes: int,
    ) -> NDArray[np.int64]:
        """Compute confusion matrix."""
        matrix = np.zeros((num_classes, num_classes), dtype=np.int64)
        for t, p in zip(y_true, y_pred):
            matrix[t, p] += 1
        return matrix
    
    def _save_results(self, result: EvaluationPipelineResult) -> None:
        """Save evaluation results."""
        if self.config.output_dir is None:
            return
        
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as numpy
        timestamp = result.evaluated_at.strftime("%Y%m%d_%H%M%S")
        np.save(
            output_dir / f"evaluation_{timestamp}.npy",
            result.to_report().to_dict(),
            allow_pickle=True,
        )
