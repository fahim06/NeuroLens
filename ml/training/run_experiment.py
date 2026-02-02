"""
Run Experiment Script

Main entry point for running training experiments.
"""

import argparse
import logging
from pathlib import Path
from typing import Any

import yaml


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict[str, Any]:
    """Load YAML configuration file."""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Load base config if specified
    if "base" in config:
        base_path = config_path.parent / config["base"]
        base_config = load_config(base_path)
        # Merge: config overrides base
        config = deep_merge(base_config, config)
    
    return config


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def run_experiment(config: dict[str, Any], config_path: Path) -> None:
    """
    Run a training experiment.
    
    Args:
        config: Configuration dictionary
        config_path: Path to config file
    """
    # Import here to avoid circular imports
    from ml.training.utils import set_seeds, get_reproducibility_info
    from ml.training.datasets import DatasetLoader, DatasetValidator
    from ml.training.augmentations import AugmentationConfig
    from ml.training.trainers import KerasTrainer, TrainerConfig
    from ml.training.experiments import ExperimentRunner, ExperimentConfig
    from ml.training.evaluation import ModelEvaluator
    
    # Set seeds for reproducibility
    seed = config.get("reproducibility", {}).get("seed", 42)
    set_seeds(seed)
    
    logger.info("=" * 60)
    logger.info("NEUROLENS TRAINING EXPERIMENT")
    logger.info("=" * 60)
    
    # Print reproducibility info
    repro_info = get_reproducibility_info()
    logger.info(f"TensorFlow version: {repro_info.get('tensorflow_version')}")
    logger.info(f"GPU available: {repro_info.get('gpu_available')}")
    
    # Extract config sections
    model_config = config.get("model", {})
    dataset_config = config.get("dataset", {})
    training_config = config.get("training", {})
    augmentation_config = config.get("augmentation", {})
    mlflow_config = config.get("mlflow", {})
    
    # =========================================================================
    # 1. Load and Validate Dataset
    # =========================================================================
    logger.info("-" * 40)
    logger.info("Loading dataset...")
    
    loader = DatasetLoader(
        data_dir=Path(dataset_config.get("data_dir", "data")),
        target_size=tuple(dataset_config.get("image_size", [224, 224])),
    )
    
    dataset = loader.load()
    
    # Validate dataset
    validator = DatasetValidator(
        min_samples_per_class=dataset_config.get("min_samples_per_class", 10),
        max_class_imbalance_ratio=dataset_config.get("max_imbalance_ratio", 10.0),
    )
    
    validation = validator.validate(
        images=dataset.train_split.images,
        labels=dataset.train_split.labels,
        class_names=dataset.class_names,
    )
    
    if not validation.is_valid:
        logger.error("Dataset validation failed!")
        for error in validation.errors:
            logger.error(f"  - {error}")
        return
    
    logger.info(f"Dataset loaded: {len(dataset.class_names)} classes")
    logger.info(f"  Train: {len(dataset.train_split.images)} samples")
    logger.info(f"  Val: {len(dataset.val_split.images)} samples")
    logger.info(f"  Test: {len(dataset.test_split.images)} samples")
    
    # =========================================================================
    # 2. Set Up Augmentation
    # =========================================================================
    logger.info("-" * 40)
    logger.info("Setting up augmentation...")
    
    aug_config = None
    if augmentation_config.get("enabled", True):
        aug_config = AugmentationConfig(
            horizontal_flip=augmentation_config.get("horizontal_flip", True),
            vertical_flip=augmentation_config.get("vertical_flip", False),
            rotation_range=augmentation_config.get("rotation_range", 20.0),
            zoom_range=augmentation_config.get("zoom_range", 0.15),
            brightness_range=augmentation_config.get("brightness_range", 0.1),
            width_shift_range=augmentation_config.get("width_shift_range", 0.1),
            height_shift_range=augmentation_config.get("height_shift_range", 0.1),
        )
        logger.info("Augmentation enabled")
    
    # =========================================================================
    # 3. Initialize Trainer and Build Model
    # =========================================================================
    logger.info("-" * 40)
    logger.info("Building model...")
    
    trainer_config = TrainerConfig.from_dict(config)
    trainer = KerasTrainer(trainer_config, augmentation_config=aug_config)
    
    input_shape = (*tuple(dataset_config.get("image_size", [224, 224])), 3)
    num_classes = len(dataset.class_names)
    
    model = trainer.build_model(
        input_shape=input_shape,
        num_classes=num_classes,
        architecture=model_config.get("architecture", "efficientnet_b0"),
        pretrained=model_config.get("pretrained", True),
        pretrained_weights=model_config.get("pretrained_weights", "imagenet"),
    )
    
    logger.info(f"Model: {model.name}")
    logger.info(f"Input shape: {input_shape}")
    logger.info(f"Output classes: {num_classes}")
    logger.info(f"Total parameters: {model.count_params():,}")
    
    # =========================================================================
    # 4. Initialize MLflow Experiment
    # =========================================================================
    logger.info("-" * 40)
    logger.info("Setting up experiment tracking...")
    
    exp_config = ExperimentConfig.from_dict(config)
    experiment = ExperimentRunner(exp_config)
    
    run_name = f"{model_config.get('architecture', 'model')}_{seed}"
    
    with experiment.start_run(run_name):
        # Log configuration
        experiment.log_params(config)
        experiment.log_config(config_path)
        
        # Log dataset info
        experiment.log_params({
            "num_classes": num_classes,
            "train_samples": len(dataset.train_split.images),
            "val_samples": len(dataset.val_split.images),
            "test_samples": len(dataset.test_split.images),
        })
        
        # =====================================================================
        # 5. Phase 1: Train with Frozen Backbone
        # =====================================================================
        logger.info("-" * 40)
        logger.info("Phase 1: Training with frozen backbone...")
        
        train_data = (dataset.train_split.images, dataset.train_split.labels)
        val_data = (dataset.val_split.images, dataset.val_split.labels)
        
        history = trainer.train(model, train_data, val_data)
        
        logger.info(f"Phase 1 completed in {history.training_time_seconds:.1f}s")
        logger.info(f"Best epoch: {history.best_epoch}")
        
        # Log phase 1 metrics
        experiment.log_training_history({
            "phase1_" + k: v for k, v in history.to_dict().items()
            if isinstance(v, list)
        })
        
        # =====================================================================
        # 6. Phase 2: Fine-tune Backbone (if enabled)
        # =====================================================================
        fine_tune_config = config.get("fine_tune", {})
        if fine_tune_config.get("enabled", False):
            logger.info("-" * 40)
            logger.info("Phase 2: Fine-tuning backbone...")
            
            trainer.unfreeze_backbone(
                model,
                num_layers=fine_tune_config.get("unfreeze_layers", 20),
                new_lr=fine_tune_config.get("learning_rate", 1e-5),
            )
            
            # Update trainer config for fine-tuning
            trainer.config.epochs = fine_tune_config.get("epochs", 50)
            trainer.config.early_stopping_patience = fine_tune_config.get("patience", 10)
            
            history2 = trainer.train(model, train_data, val_data)
            
            logger.info(f"Phase 2 completed in {history2.training_time_seconds:.1f}s")
            
            # Log phase 2 metrics
            experiment.log_training_history({
                "phase2_" + k: v for k, v in history2.to_dict().items()
                if isinstance(v, list)
            })
        
        # =====================================================================
        # 7. Evaluate on Test Set
        # =====================================================================
        logger.info("-" * 40)
        logger.info("Evaluating on test set...")
        
        evaluator = ModelEvaluator(class_names=dataset.class_names)
        result = evaluator.evaluate(
            model,
            dataset.test_split.images,
            dataset.test_split.labels,
        )
        
        # Print report
        evaluator.print_report(result)
        evaluator.print_confusion_matrix(result)
        
        # Log evaluation metrics
        experiment.log_metrics({
            "test_accuracy": result.accuracy,
            "test_macro_f1": result.macro_f1,
            "test_weighted_f1": result.weighted_f1,
            "test_macro_precision": result.macro_precision,
            "test_macro_recall": result.macro_recall,
        })
        
        # Log evaluation results
        experiment.log_dict(result.to_dict(), "evaluation_results.json")
        
        # =====================================================================
        # 8. Save Model
        # =====================================================================
        logger.info("-" * 40)
        logger.info("Saving model...")
        
        output_dir = Path(config.get("output", {}).get("dir", "outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = output_dir / f"{run_name}.keras"
        trainer.save_model(model, model_path)
        
        # Log model as artifact
        experiment.log_artifact(model_path, "model")
        
        # Save evaluation results
        result.save(output_dir / f"{run_name}_evaluation.json")
        
        logger.info("=" * 60)
        logger.info("EXPERIMENT COMPLETE")
        logger.info(f"Test Accuracy: {result.accuracy:.4f}")
        logger.info(f"Model saved to: {model_path}")
        logger.info("=" * 60)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run NeuroLens training experiment")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        return
    
    config = load_config(args.config)
    run_experiment(config, args.config)


if __name__ == "__main__":
    main()
