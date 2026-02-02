"""
Keras Trainer

Trainer implementation for TensorFlow/Keras models.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ml.training.trainers.base_trainer import (
    BaseModelTrainer,
    TrainerConfig,
    TrainingHistory,
)
from ml.training.augmentations import AugmentationConfig, create_tf_augmentation_layer


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None
    keras = None


class KerasTrainer(BaseModelTrainer):
    """
    Trainer for TensorFlow/Keras models.
    
    Supports:
    - Custom CNN and transfer learning models
    - Data augmentation via tf.keras layers
    - Learning rate scheduling
    - Early stopping
    - Checkpointing
    - MLflow integration (via callbacks)
    
    Example:
        >>> config = TrainerConfig(epochs=100, batch_size=32)
        >>> trainer = KerasTrainer(config)
        >>> history = trainer.train(model, train_data, val_data)
    """
    
    def __init__(
        self,
        config: TrainerConfig,
        augmentation_config: AugmentationConfig | None = None,
    ) -> None:
        """
        Initialize Keras trainer.
        
        Args:
            config: Training configuration
            augmentation_config: Optional augmentation configuration
        """
        if not HAS_TF:
            raise ImportError("TensorFlow is required for KerasTrainer")
        
        super().__init__(config)
        self.augmentation_config = augmentation_config
        self._model: keras.Model | None = None
    
    def build_model(
        self,
        input_shape: tuple[int, int, int],
        num_classes: int,
        architecture: str = "custom_cnn",
        pretrained: bool = False,
        pretrained_weights: str = "imagenet",
    ) -> keras.Model:
        """
        Build a Keras model.
        
        Args:
            input_shape: Input shape (H, W, C)
            num_classes: Number of output classes
            architecture: Model architecture name
            pretrained: Whether to use pretrained weights
            pretrained_weights: Pretrained weights source
        
        Returns:
            Compiled Keras model
        """
        if architecture == "efficientnet_b0":
            model = self._build_efficientnet(
                input_shape,
                num_classes,
                pretrained,
                pretrained_weights,
            )
        elif architecture == "mobilenet_v2":
            model = self._build_mobilenet(
                input_shape,
                num_classes,
                pretrained,
                pretrained_weights,
            )
        else:
            model = self._build_custom_cnn(input_shape, num_classes)
        
        # Compile model
        optimizer = self._get_optimizer()
        model.compile(
            optimizer=optimizer,
            loss=self.config.loss,
            metrics=self.config.metrics,
        )
        
        self._model = model
        return model
    
    def _build_custom_cnn(
        self,
        input_shape: tuple[int, int, int],
        num_classes: int,
    ) -> keras.Model:
        """Build a custom CNN architecture."""
        inputs = keras.Input(shape=input_shape)
        
        # Optional augmentation layer
        x = inputs
        if self.augmentation_config:
            aug_layer = create_tf_augmentation_layer(self.augmentation_config)
            x = aug_layer(x)
        
        # Convolutional blocks
        x = keras.layers.Conv2D(32, 3, padding="same", activation="relu")(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.MaxPooling2D()(x)
        
        x = keras.layers.Conv2D(64, 3, padding="same", activation="relu")(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.MaxPooling2D()(x)
        
        x = keras.layers.Conv2D(128, 3, padding="same", activation="relu")(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.MaxPooling2D()(x)
        
        x = keras.layers.Conv2D(256, 3, padding="same", activation="relu")(x)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.GlobalAveragePooling2D()(x)
        
        # Classification head
        x = keras.layers.Dense(256, activation="relu")(x)
        x = keras.layers.Dropout(0.5)(x)
        outputs = keras.layers.Dense(num_classes, activation="softmax")(x)
        
        return keras.Model(inputs, outputs, name="custom_cnn")
    
    def _build_efficientnet(
        self,
        input_shape: tuple[int, int, int],
        num_classes: int,
        pretrained: bool,
        pretrained_weights: str,
    ) -> keras.Model:
        """Build EfficientNet-B0 with transfer learning."""
        weights = pretrained_weights if pretrained else None
        
        base_model = keras.applications.EfficientNetB0(
            include_top=False,
            weights=weights,
            input_shape=input_shape,
            pooling="avg",
        )
        
        # Freeze base model initially
        base_model.trainable = False
        
        inputs = keras.Input(shape=input_shape)
        
        # Optional augmentation
        x = inputs
        if self.augmentation_config:
            aug_layer = create_tf_augmentation_layer(self.augmentation_config)
            x = aug_layer(x)
        
        # EfficientNet preprocessing
        x = keras.applications.efficientnet.preprocess_input(x * 255)
        
        x = base_model(x, training=False)
        x = keras.layers.Dropout(0.3)(x)
        outputs = keras.layers.Dense(num_classes, activation="softmax")(x)
        
        model = keras.Model(inputs, outputs, name="efficientnet_b0")
        model.base_model = base_model  # Store reference for fine-tuning
        
        return model
    
    def _build_mobilenet(
        self,
        input_shape: tuple[int, int, int],
        num_classes: int,
        pretrained: bool,
        pretrained_weights: str,
    ) -> keras.Model:
        """Build MobileNetV2 with transfer learning."""
        weights = pretrained_weights if pretrained else None
        
        base_model = keras.applications.MobileNetV2(
            include_top=False,
            weights=weights,
            input_shape=input_shape,
            pooling="avg",
        )
        
        base_model.trainable = False
        
        inputs = keras.Input(shape=input_shape)
        x = inputs
        
        if self.augmentation_config:
            aug_layer = create_tf_augmentation_layer(self.augmentation_config)
            x = aug_layer(x)
        
        x = keras.applications.mobilenet_v2.preprocess_input(x * 255)
        x = base_model(x, training=False)
        x = keras.layers.Dropout(0.3)(x)
        outputs = keras.layers.Dense(num_classes, activation="softmax")(x)
        
        model = keras.Model(inputs, outputs, name="mobilenet_v2")
        model.base_model = base_model
        
        return model
    
    def _get_optimizer(self) -> keras.optimizers.Optimizer:
        """Get optimizer from config."""
        if self.config.optimizer.lower() == "adam":
            return keras.optimizers.Adam(learning_rate=self.config.learning_rate)
        elif self.config.optimizer.lower() == "sgd":
            return keras.optimizers.SGD(
                learning_rate=self.config.learning_rate,
                momentum=0.9,
            )
        elif self.config.optimizer.lower() == "adamw":
            return keras.optimizers.AdamW(learning_rate=self.config.learning_rate)
        else:
            return keras.optimizers.Adam(learning_rate=self.config.learning_rate)
    
    def _get_callbacks(self) -> list[keras.callbacks.Callback]:
        """Get training callbacks."""
        callbacks = []
        
        # Early stopping
        if self.config.early_stopping_patience > 0:
            callbacks.append(keras.callbacks.EarlyStopping(
                monitor=self.config.early_stopping_monitor,
                patience=self.config.early_stopping_patience,
                mode=self.config.early_stopping_mode,
                restore_best_weights=self.config.restore_best_weights,
                verbose=1,
            ))
        
        # Learning rate reduction
        if self.config.lr_reduce_patience > 0:
            callbacks.append(keras.callbacks.ReduceLROnPlateau(
                monitor=self.config.early_stopping_monitor,
                factor=self.config.lr_reduce_factor,
                patience=self.config.lr_reduce_patience,
                min_lr=self.config.min_lr,
                verbose=1,
            ))
        
        # Checkpointing
        if self.config.checkpoint_dir:
            checkpoint_path = self.config.checkpoint_dir / "model_{epoch:03d}.keras"
            self.config.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            callbacks.append(keras.callbacks.ModelCheckpoint(
                str(checkpoint_path),
                save_best_only=True,
                monitor=self.config.early_stopping_monitor,
                mode=self.config.early_stopping_mode,
                verbose=1,
            ))
        
        return callbacks
    
    def train(
        self,
        model: keras.Model,
        train_data: tuple[NDArray[np.float32], NDArray[np.int64]] | tf.data.Dataset,
        val_data: tuple[NDArray[np.float32], NDArray[np.int64]] | tf.data.Dataset | None = None,
    ) -> TrainingHistory:
        """
        Train the Keras model.
        
        Args:
            model: Keras model to train
            train_data: Training data (images, labels) or tf.data.Dataset
            val_data: Validation data
        
        Returns:
            TrainingHistory with all metrics
        """
        logger.info(f"Starting training for {self.config.epochs} epochs")
        start_time = time.time()
        
        # Convert to appropriate format
        if isinstance(train_data, tuple):
            train_images, train_labels = train_data
            # One-hot encode labels
            num_classes = model.output_shape[-1]
            train_labels_onehot = keras.utils.to_categorical(train_labels, num_classes)
            train_dataset = (train_images, train_labels_onehot)
        else:
            train_dataset = train_data
        
        val_dataset = None
        if val_data is not None:
            if isinstance(val_data, tuple):
                val_images, val_labels = val_data
                num_classes = model.output_shape[-1]
                val_labels_onehot = keras.utils.to_categorical(val_labels, num_classes)
                val_dataset = (val_images, val_labels_onehot)
            else:
                val_dataset = val_data
        
        # Get callbacks
        callbacks = self._get_callbacks()
        
        # Train
        history = model.fit(
            train_dataset[0] if isinstance(train_dataset, tuple) else train_dataset,
            train_dataset[1] if isinstance(train_dataset, tuple) else None,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            validation_data=val_dataset,
            callbacks=callbacks,
            verbose=self.config.verbose,
        )
        
        training_time = time.time() - start_time
        
        # Build history object
        training_history = TrainingHistory(
            train_loss=history.history.get("loss", []),
            val_loss=history.history.get("val_loss", []),
            train_metrics={
                k: v for k, v in history.history.items()
                if not k.startswith("val_") and k != "loss"
            },
            val_metrics={
                k.replace("val_", ""): v
                for k, v in history.history.items()
                if k.startswith("val_") and k != "val_loss"
            },
            epochs_trained=len(history.history.get("loss", [])),
            training_time_seconds=training_time,
            early_stopped=len(history.history.get("loss", [])) < self.config.epochs,
        )
        
        # Find best epoch
        if training_history.val_loss:
            if self.config.early_stopping_mode == "min":
                training_history.best_epoch = int(np.argmin(training_history.val_loss)) + 1
                training_history.best_val_metric = min(training_history.val_loss)
            else:
                if "accuracy" in training_history.val_metrics:
                    training_history.best_epoch = int(np.argmax(training_history.val_metrics["accuracy"])) + 1
                    training_history.best_val_metric = max(training_history.val_metrics["accuracy"])
        
        training_history.completed_at = datetime.utcnow()
        
        self._history = training_history
        self._model = model
        
        logger.info(
            f"Training completed in {training_time:.1f}s. "
            f"Best epoch: {training_history.best_epoch}"
        )
        
        return training_history
    
    def evaluate(
        self,
        model: keras.Model,
        test_data: tuple[NDArray[np.float32], NDArray[np.int64]] | tf.data.Dataset,
    ) -> dict[str, float]:
        """
        Evaluate model on test data.
        
        Args:
            model: Trained model
            test_data: Test data
        
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model on test data")
        
        if isinstance(test_data, tuple):
            test_images, test_labels = test_data
            num_classes = model.output_shape[-1]
            test_labels_onehot = keras.utils.to_categorical(test_labels, num_classes)
            results = model.evaluate(
                test_images,
                test_labels_onehot,
                verbose=0,
            )
        else:
            results = model.evaluate(test_data, verbose=0)
        
        metric_names = model.metrics_names
        metrics = dict(zip(metric_names, results))
        
        logger.info(f"Test metrics: {metrics}")
        return metrics
    
    def save_model(self, model: keras.Model, path: Path) -> None:
        """Save model to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(path))
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: Path) -> keras.Model:
        """Load model from disk."""
        model = keras.models.load_model(str(path))
        logger.info(f"Model loaded from {path}")
        return model
    
    def unfreeze_backbone(
        self,
        model: keras.Model,
        num_layers: int = 20,
        new_lr: float | None = None,
    ) -> None:
        """
        Unfreeze backbone layers for fine-tuning.
        
        Args:
            model: Model with frozen backbone
            num_layers: Number of layers to unfreeze from the end
            new_lr: New learning rate (optional, typically lower)
        """
        if hasattr(model, "base_model"):
            base_model = model.base_model
            base_model.trainable = True
            
            # Freeze all except last num_layers
            for layer in base_model.layers[:-num_layers]:
                layer.trainable = False
            
            logger.info(f"Unfroze last {num_layers} layers of backbone")
            
            # Recompile with new learning rate
            if new_lr:
                model.compile(
                    optimizer=keras.optimizers.Adam(learning_rate=new_lr),
                    loss=self.config.loss,
                    metrics=self.config.metrics,
                )
                logger.info(f"Recompiled with learning rate {new_lr}")
