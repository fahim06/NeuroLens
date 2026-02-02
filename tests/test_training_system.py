"""
Test Phase 5 Training System

Quick verification that all training components work correctly.
"""

import sys
sys.path.insert(0, "/Users/fahim/Documents/Others/NeuroLens")

def test_training_system():
    """Test all training system components."""
    
    print("Testing Phase 5: Training System")
    print("=" * 50)
    
    # Test imports
    print("\n1. Testing imports...")
    from ml.training import (
        KerasTrainer, TrainerConfig, TrainingHistory,
        DatasetLoader, DatasetValidator,
        ImageAugmentor, AugmentationConfig,
        ExperimentRunner, ExperimentConfig,
        ModelEvaluator, EvaluationResult,
        set_seeds, create_callbacks,
    )
    print("   ✓ All training components imported")
    
    # Test TensorFlow
    import tensorflow as tf
    print(f"   ✓ TensorFlow {tf.__version__}")
    
    # Test MLflow
    import mlflow
    print(f"   ✓ MLflow {mlflow.__version__}")
    
    # Test GPU
    gpus = tf.config.list_physical_devices("GPU")
    print(f"   ✓ GPU devices: {len(gpus)}")
    
    # Test seeds
    print("\n2. Testing reproducibility utils...")
    set_seeds(42)
    print("   ✓ Seeds set successfully")
    
    # Test augmentation config
    print("\n3. Testing augmentation...")
    aug_config = AugmentationConfig(
        horizontal_flip=True,
        rotation_range=20.0,
        zoom_range=0.15,
    )
    print(f"   ✓ AugmentationConfig created")
    
    # Test trainer config
    print("\n4. Testing trainer config...")
    trainer_config = TrainerConfig(epochs=10, batch_size=32)
    print(f"   ✓ TrainerConfig: epochs={trainer_config.epochs}, batch={trainer_config.batch_size}")
    
    # Test KerasTrainer
    print("\n5. Testing KerasTrainer...")
    trainer = KerasTrainer(trainer_config)
    print("   ✓ KerasTrainer initialized")
    
    # Test model building
    print("\n6. Testing model building...")
    model = trainer.build_model(
        input_shape=(224, 224, 3),
        num_classes=4,
        architecture="custom_cnn",
    )
    print(f"   ✓ Model: {model.name}")
    print(f"   ✓ Parameters: {model.count_params():,}")
    
    # Test EfficientNet
    print("\n7. Testing EfficientNet transfer learning...")
    trainer2 = KerasTrainer(TrainerConfig(epochs=5))
    effnet = trainer2.build_model(
        input_shape=(224, 224, 3),
        num_classes=4,
        architecture="efficientnet_b0",
        pretrained=True,
    )
    print(f"   ✓ EfficientNet: {effnet.name}")
    print(f"   ✓ Parameters: {effnet.count_params():,}")
    
    # Test evaluator
    print("\n8. Testing ModelEvaluator...")
    evaluator = ModelEvaluator(class_names=["Class1", "Class2", "Class3", "Class4"])
    print("   ✓ ModelEvaluator initialized")
    
    print("\n" + "=" * 50)
    print("PHASE 5 TRAINING SYSTEM: ALL TESTS PASSED ✓")
    print("=" * 50)


if __name__ == "__main__":
    test_training_system()
