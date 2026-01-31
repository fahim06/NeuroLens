"""
Training Pipeline

Orchestrates the complete training workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

from ml.core.interfaces.model import BaseModel
from ml.core.interfaces.trainer import BaseTrainer, TrainingConfig, TrainingResult
from ml.core.interfaces.evaluator import BaseEvaluator, EvaluationResult
from ml.core.registry import ModelRegistry, ModelRecord
from ml.core.schemas.metrics import TrainingMetrics
from ml.pipelines.preprocess import PreprocessingPipeline, PipelineConfig


M = TypeVar("M", bound=BaseModel)


@dataclass
class TrainingPipelineConfig:
    """
    Configuration for training pipeline.
    
    Attributes:
        training_config: Model training configuration
        preprocess_config: Preprocessing configuration
        experiment_name: Name for this training run
        checkpoint_dir: Directory for checkpoints
        save_best_only: Only save best model
        evaluate_after_training: Run evaluation after training
        register_model: Register model after training
        seed: Random seed for reproducibility
    """
    
    training_config: TrainingConfig = field(default_factory=TrainingConfig)
    preprocess_config: PipelineConfig = field(default_factory=PipelineConfig)
    experiment_name: str = ""
    checkpoint_dir: Path | None = None
    save_best_only: bool = True
    evaluate_after_training: bool = True
    register_model: bool = False
    seed: int = 42


@dataclass
class TrainingPipelineResult:
    """
    Complete result from training pipeline.
    
    Attributes:
        training_result: Result from trainer
        evaluation_result: Optional evaluation result
        model_record: Optional registry record
        experiment_name: Experiment identifier
        artifacts_path: Path to saved artifacts
        started_at: Pipeline start time
        completed_at: Pipeline completion time
    """
    
    training_result: TrainingResult
    evaluation_result: EvaluationResult | None = None
    model_record: ModelRecord | None = None
    experiment_name: str = ""
    artifacts_path: Path | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    @property
    def duration_seconds(self) -> float:
        """Total pipeline duration."""
        if self.completed_at is None:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()


class TrainingPipeline(Generic[M]):
    """
    Complete training pipeline orchestrator.
    
    Flow:
        Raw Data → Validation → Preprocess → Train → Evaluate → Register
    
    Example:
        >>> pipeline = TrainingPipeline(model, trainer, config)
        >>> result = pipeline.run(train_data, val_data, test_data)
    """
    
    def __init__(
        self,
        model: M,
        trainer: BaseTrainer[M],
        config: TrainingPipelineConfig | None = None,
        evaluator: BaseEvaluator[M] | None = None,
        registry: ModelRegistry | None = None,
    ) -> None:
        """
        Initialize training pipeline.
        
        Args:
            model: Model to train
            trainer: Trainer instance
            config: Pipeline configuration
            evaluator: Optional evaluator
            registry: Optional model registry
        """
        self.model = model
        self.trainer = trainer
        self.config = config or TrainingPipelineConfig()
        self.evaluator = evaluator
        self.registry = registry
        
        # Initialize preprocessing pipeline
        self._preprocess_pipeline = PreprocessingPipeline(
            config=self.config.preprocess_config,
            mode="training",
        )
        
        # Generate experiment name if not provided
        if not self.config.experiment_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            self.config.experiment_name = f"{model.name}_{timestamp}"
    
    def run(
        self,
        train_data: Any,
        val_data: Any | None = None,
        test_data: Any | None = None,
    ) -> TrainingPipelineResult:
        """
        Run complete training pipeline.
        
        Args:
            train_data: Training dataset
            val_data: Validation dataset
            test_data: Test dataset for final evaluation
        
        Returns:
            TrainingPipelineResult with all outputs
        """
        started_at = datetime.utcnow()
        
        # Set random seed for reproducibility
        self._set_seed(self.config.seed)
        
        # Fit preprocessing on training data
        self._preprocess_pipeline.fit(train_data)
        
        # Preprocess data
        train_processed = self._preprocess_pipeline.transform(train_data)
        val_processed = (
            self._preprocess_pipeline.transform(val_data)
            if val_data is not None
            else None
        )
        
        # Train model
        training_result = self.trainer.train(
            train_data=train_processed,
            val_data=val_processed,
        )
        
        # Evaluate if enabled and evaluator provided
        evaluation_result = None
        if (
            self.config.evaluate_after_training
            and self.evaluator is not None
            and test_data is not None
        ):
            test_processed = self._preprocess_pipeline.transform(test_data)
            evaluation_result = self.evaluator.evaluate(
                self.model,
                test_processed,
            )
        
        # Save artifacts
        artifacts_path = self._save_artifacts(training_result)
        
        # Register model if enabled
        model_record = None
        if self.config.register_model and self.registry is not None:
            model_record = self._register_model(
                training_result,
                evaluation_result,
            )
        
        completed_at = datetime.utcnow()
        
        return TrainingPipelineResult(
            training_result=training_result,
            evaluation_result=evaluation_result,
            model_record=model_record,
            experiment_name=self.config.experiment_name,
            artifacts_path=artifacts_path,
            started_at=started_at,
            completed_at=completed_at,
        )
    
    def _set_seed(self, seed: int) -> None:
        """Set random seed for reproducibility."""
        np.random.seed(seed)
        # Framework-specific seeding handled in trainer
    
    def _save_artifacts(self, result: TrainingResult) -> Path | None:
        """Save training artifacts."""
        if self.config.checkpoint_dir is None:
            return None
        
        artifacts_dir = self.config.checkpoint_dir / self.config.experiment_name
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = artifacts_dir / f"{self.model.name}.model"
        self.model.save(model_path)
        
        # Save preprocessor
        preprocess_path = artifacts_dir / "preprocessor.npy"
        self._preprocess_pipeline.save(preprocess_path)
        
        # Save config
        config_path = artifacts_dir / "config.npy"
        np.save(config_path, {
            "training": self.config.training_config.to_dict(),
            "experiment": self.config.experiment_name,
            "seed": self.config.seed,
        }, allow_pickle=True)
        
        return artifacts_dir
    
    def _register_model(
        self,
        training_result: TrainingResult,
        evaluation_result: EvaluationResult | None,
    ) -> ModelRecord | None:
        """Register trained model."""
        if self.registry is None:
            return None
        
        from ml.core.registry.metadata import ModelFramework
        
        metrics = training_result.best_metrics.copy()
        if evaluation_result:
            metrics.update(evaluation_result.metrics)
        
        return self.registry.register(
            name=self.model.name,
            version=self.model.version,
            framework=ModelFramework(self.model.metadata.framework),
            model_path=training_result.model_path or Path("."),
            input_schema={"shape": list(self.model.input_shape)},
            output_schema={"classes": list(self.model.output_classes)},
            metrics=metrics,
        )
