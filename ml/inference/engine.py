"""
Inference Engine

Main inference engine that orchestrates the full prediction pipeline.
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ml.inference.loader import ModelLoader, ArtifactBundle
from ml.inference.preprocessor import InferencePreprocessor, PreprocessorConfig
from ml.inference.batcher import InferenceBatcher, BatchConfig
from ml.inference.postprocess import Postprocessor, PredictionOutput
from ml.inference.calibration import TemperatureScaler


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None
    keras = None


@dataclass
class InferenceResult:
    """
    Complete inference result.
    
    Attributes:
        prediction: Main prediction output
        latency_ms: Inference latency in milliseconds
        preprocessor_ms: Preprocessing latency
        model_ms: Model inference latency
        postprocessor_ms: Postprocessing latency
        batch_size: Batch size used
        metadata: Additional metadata
    """
    
    prediction: PredictionOutput
    latency_ms: float = 0.0
    preprocessor_ms: float = 0.0
    model_ms: float = 0.0
    postprocessor_ms: float = 0.0
    batch_size: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prediction": self.prediction.to_dict(),
            "latency_ms": self.latency_ms,
            "preprocessor_ms": self.preprocessor_ms,
            "model_ms": self.model_ms,
            "postprocessor_ms": self.postprocessor_ms,
            "batch_size": self.batch_size,
            "metadata": self.metadata,
        }


@dataclass
class BatchInferenceResult:
    """
    Batch inference result.
    
    Attributes:
        predictions: List of prediction outputs
        total_latency_ms: Total inference latency
        throughput: Images per second
    """
    
    predictions: list[PredictionOutput]
    total_latency_ms: float = 0.0
    throughput: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "predictions": [p.to_dict() for p in self.predictions],
            "total_latency_ms": self.total_latency_ms,
            "throughput": self.throughput,
            "count": len(self.predictions),
        }


class InferenceEngine:
    """
    Main inference engine.
    
    Orchestrates the full prediction pipeline:
    Input → Preprocess → Batch → Predict → Calibrate → Postprocess → Output
    
    Features:
    - Frozen preprocessing
    - Efficient batching
    - Confidence calibration
    - Latency tracking
    - Device-aware execution
    
    Example:
        >>> engine = InferenceEngine.from_checkpoint("model.keras")
        >>> result = engine.predict(image)
        >>> print(result.prediction.class_name)
        
        # Batch inference
        >>> results = engine.predict_batch(images)
    """
    
    def __init__(
        self,
        model: keras.Model,
        class_names: list[str],
        preprocessor_config: PreprocessorConfig | None = None,
        batch_config: BatchConfig | None = None,
        calibration_temperature: float = 1.0,
    ) -> None:
        """
        Initialize inference engine.
        
        Args:
            model: Loaded Keras model
            class_names: List of class names
            preprocessor_config: Preprocessing configuration
            batch_config: Batching configuration
            calibration_temperature: Calibration temperature
        """
        if not HAS_TF:
            raise ImportError("TensorFlow is required for InferenceEngine")
        
        self.model = model
        self.class_names = class_names
        
        # Get input shape from model
        input_shape = model.input_shape[1:]
        
        # Initialize components
        if preprocessor_config is None:
            preprocessor_config = PreprocessorConfig(
                target_size=(input_shape[0], input_shape[1]),
            )
        
        self.preprocessor = InferencePreprocessor(preprocessor_config)
        self.batcher = InferenceBatcher(batch_config or BatchConfig())
        self.postprocessor = Postprocessor(class_names)
        self.calibration_temperature = calibration_temperature
        
        self._warm = False
        logger.info(f"InferenceEngine initialized: {len(class_names)} classes")
    
    @classmethod
    def from_checkpoint(
        cls,
        model_path: Path | str,
        metadata_path: Path | str | None = None,
        device: str = "auto",
        warm_up: bool = True,
    ) -> "InferenceEngine":
        """
        Create engine from saved checkpoint.
        
        Args:
            model_path: Path to model file
            metadata_path: Path to metadata JSON
            device: Device to use
            warm_up: Whether to run warm-up
        
        Returns:
            Initialized InferenceEngine
        """
        loader = ModelLoader(device=device, warm_up=warm_up)
        bundle = loader.load(model_path, metadata_path)
        
        preprocessor_config = None
        if bundle.preprocessor_config:
            preprocessor_config = PreprocessorConfig.from_dict(bundle.preprocessor_config)
        
        engine = cls(
            model=bundle.model,
            class_names=bundle.class_names,
            preprocessor_config=preprocessor_config,
        )
        engine._warm = warm_up
        
        return engine
    
    @classmethod
    def from_bundle(cls, bundle: ArtifactBundle) -> "InferenceEngine":
        """
        Create engine from artifact bundle.
        
        Args:
            bundle: ArtifactBundle with loaded model
        
        Returns:
            Initialized InferenceEngine
        """
        preprocessor_config = None
        if bundle.preprocessor_config:
            preprocessor_config = PreprocessorConfig.from_dict(bundle.preprocessor_config)
        
        return cls(
            model=bundle.model,
            class_names=bundle.class_names,
            preprocessor_config=preprocessor_config,
        )
    
    def predict(
        self,
        image: NDArray[np.uint8] | NDArray[np.float32] | str | Path,
        return_top_k: int | None = None,
    ) -> InferenceResult:
        """
        Predict on a single image.
        
        Args:
            image: Image array or file path
            return_top_k: If set, include top-k predictions
        
        Returns:
            InferenceResult with prediction
        """
        start_time = time.perf_counter()
        
        # Preprocess
        preprocess_start = time.perf_counter()
        processed = self.preprocessor.process(image)
        preprocess_time = (time.perf_counter() - preprocess_start) * 1000
        
        # Add batch dimension
        batch = np.expand_dims(processed, axis=0)
        
        # Model inference
        model_start = time.perf_counter()
        output = self.model.predict(batch, verbose=0)
        model_time = (time.perf_counter() - model_start) * 1000
        
        # Postprocess
        postprocess_start = time.perf_counter()
        prediction = self.postprocessor.process(
            output[0],
            calibration_temperature=self.calibration_temperature,
        )
        postprocess_time = (time.perf_counter() - postprocess_start) * 1000
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        result = InferenceResult(
            prediction=prediction,
            latency_ms=total_time,
            preprocessor_ms=preprocess_time,
            model_ms=model_time,
            postprocessor_ms=postprocess_time,
            batch_size=1,
        )
        
        if return_top_k:
            result.metadata["top_k"] = prediction.top_k[:return_top_k]
        
        return result
    
    def predict_batch(
        self,
        images: list[NDArray[np.uint8] | NDArray[np.float32] | str | Path],
    ) -> BatchInferenceResult:
        """
        Predict on a batch of images.
        
        Args:
            images: List of images or file paths
        
        Returns:
            BatchInferenceResult with all predictions
        """
        start_time = time.perf_counter()
        
        # Preprocess all images
        processed = self.preprocessor.process_batch(images)
        
        # Run batched inference
        all_predictions = []
        
        for batch, actual_size in self.batcher.batch(processed):
            outputs = self.model.predict(batch, verbose=0)
            
            # Postprocess each output
            for i in range(actual_size):
                prediction = self.postprocessor.process(
                    outputs[i],
                    calibration_temperature=self.calibration_temperature,
                )
                all_predictions.append(prediction)
        
        total_time = (time.perf_counter() - start_time) * 1000
        throughput = len(images) / (total_time / 1000) if total_time > 0 else 0
        
        return BatchInferenceResult(
            predictions=all_predictions,
            total_latency_ms=total_time,
            throughput=throughput,
        )
    
    def predict_with_gradcam(
        self,
        image: NDArray[np.uint8] | NDArray[np.float32] | str | Path,
        layer_name: str | None = None,
    ) -> tuple[InferenceResult, Any]:
        """
        Predict with Grad-CAM explanation.
        
        Args:
            image: Image array or file path
            layer_name: Convolutional layer to use
        
        Returns:
            Tuple of (InferenceResult, GradCAMResult)
        """
        from ml.inference.explainability import GradCAM
        
        # Get prediction first
        result = self.predict(image)
        
        # Compute Grad-CAM
        processed = self.preprocessor.process(image)
        gradcam = GradCAM(self.model, layer_name, self.class_names)
        gradcam_result = gradcam.compute_with_overlay(
            processed,
            class_idx=result.prediction.class_idx,
        )
        
        return result, gradcam_result
    
    def set_calibration(
        self,
        temperature: float | None = None,
        scaler: TemperatureScaler | None = None,
    ) -> None:
        """
        Set calibration parameters.
        
        Args:
            temperature: Temperature value
            scaler: Fitted TemperatureScaler
        """
        if scaler is not None:
            self.calibration_temperature = scaler.temperature
        elif temperature is not None:
            self.calibration_temperature = temperature
        
        logger.info(f"Calibration temperature set to {self.calibration_temperature}")
    
    def warm_up(self, n_runs: int = 3) -> float:
        """
        Run warm-up inference.
        
        Args:
            n_runs: Number of warm-up runs
        
        Returns:
            Average latency in ms
        """
        logger.info(f"Running {n_runs} warm-up inference(s)...")
        
        # Create dummy input
        input_shape = self.model.input_shape[1:]
        dummy = np.zeros((1, *input_shape), dtype=np.float32)
        
        latencies = []
        for _ in range(n_runs):
            start = time.perf_counter()
            _ = self.model.predict(dummy, verbose=0)
            latencies.append((time.perf_counter() - start) * 1000)
        
        avg_latency = np.mean(latencies)
        self._warm = True
        
        logger.info(f"Warm-up complete. Avg latency: {avg_latency:.2f}ms")
        return float(avg_latency)
    
    def benchmark(
        self,
        n_samples: int = 100,
        batch_sizes: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Benchmark inference performance.
        
        Args:
            n_samples: Number of samples to test
            batch_sizes: Batch sizes to test
        
        Returns:
            Benchmark results
        """
        if batch_sizes is None:
            batch_sizes = [1, 8, 16, 32]
        
        input_shape = self.model.input_shape[1:]
        results = {}
        
        for batch_size in batch_sizes:
            # Generate dummy data
            dummy = np.random.rand(n_samples, *input_shape).astype(np.float32)
            
            # Warm up
            _ = self.model.predict(dummy[:batch_size], verbose=0)
            
            # Benchmark
            start = time.perf_counter()
            for i in range(0, n_samples, batch_size):
                batch = dummy[i:i + batch_size]
                _ = self.model.predict(batch, verbose=0)
            total_time = time.perf_counter() - start
            
            throughput = n_samples / total_time
            latency_per_image = (total_time / n_samples) * 1000
            
            results[f"batch_{batch_size}"] = {
                "throughput": throughput,
                "latency_ms": latency_per_image,
                "total_time_s": total_time,
            }
            
            logger.info(
                f"Batch {batch_size}: {throughput:.1f} img/s, "
                f"{latency_per_image:.2f}ms/img"
            )
        
        return results
    
    @property
    def input_shape(self) -> tuple[int, ...]:
        """Get model input shape."""
        return self.model.input_shape[1:]
    
    @property
    def num_classes(self) -> int:
        """Get number of classes."""
        return len(self.class_names)
