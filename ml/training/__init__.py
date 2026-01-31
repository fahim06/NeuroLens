"""
NeuroLens Training System

Training engine for producing high-quality models using the ML core interfaces.

Architecture:
    - configs/: YAML configuration files
    - datasets/: Dataset loading and validation
    - augmentations/: Image augmentation pipelines
    - trainers/: Model trainers (BaseTrainer, KerasTrainer)
    - experiments/: MLflow experiment tracking
    - evaluation/: Model evaluation and metrics
    - utils/: Seeds, callbacks, utilities

Usage:
    # Run an experiment from command line
    python -m ml.training.run_experiment --config ml/training/configs/efficientnet.yaml

    # Or use programmatically
    from ml.training import KerasTrainer, DatasetLoader, ExperimentRunner
    
    loader = DatasetLoader(data_dir="path/to/data")
    dataset = loader.load()
    
    trainer = KerasTrainer(config)
    model = trainer.build_model(input_shape, num_classes)
    history = trainer.train(model, train_data, val_data)
"""

from ml.training.trainers import (
    KerasTrainer,
    BaseModelTrainer,
    TrainerConfig,
    TrainingHistory,
)
from ml.training.datasets import (
    DatasetLoader,
    DatasetValidator,
    ImageDataset,
    DatasetSplit,
    ValidationResult,
)
from ml.training.augmentations import (
    ImageAugmentor,
    AugmentationConfig,
    create_augmentation_pipeline,
    create_tf_augmentation_layer,
)
from ml.training.experiments import (
    ExperimentRunner,
    ExperimentConfig,
)
from ml.training.evaluation import (
    ModelEvaluator,
    EvaluationResult,
)
from ml.training.utils import (
    set_seeds,
    get_reproducibility_info,
    MLflowCallback,
    ProgressCallback,
    create_callbacks,
)

__all__ = [
    # Trainers
    "KerasTrainer",
    "BaseModelTrainer",
    "TrainerConfig",
    "TrainingHistory",
    # Datasets
    "DatasetLoader",
    "DatasetValidator",
    "ImageDataset",
    "DatasetSplit",
    "ValidationResult",
    # Augmentations
    "ImageAugmentor",
    "AugmentationConfig",
    "create_augmentation_pipeline",
    "create_tf_augmentation_layer",
    # Experiments
    "ExperimentRunner",
    "ExperimentConfig",
    # Evaluation
    "ModelEvaluator",
    "EvaluationResult",
    # Utils
    "set_seeds",
    "get_reproducibility_info",
    "MLflowCallback",
    "ProgressCallback",
    "create_callbacks",
]
