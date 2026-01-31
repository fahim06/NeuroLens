"""
Validation Suite

Validates inference system correctness and performance.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None


@dataclass
class ValidationResult:
    """
    Validation result.
    
    Attributes:
        passed: Whether all validations passed
        checks: Dictionary of individual check results
        errors: List of error messages
        warnings: List of warning messages
    """
    
    passed: bool = True
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    
    def add_check(self, name: str, passed: bool, message: str = "") -> None:
        """Add a check result."""
        self.checks[name] = passed
        if not passed:
            self.passed = False
            if message:
                self.errors.append(f"{name}: {message}")
    
    def add_warning(self, message: str) -> None:
        """Add a warning."""
        self.warnings.append(message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


class InferenceValidator:
    """
    Validates inference system.
    
    Checks:
    - Shape correctness
    - Numerical stability
    - Latency per batch size
    - GPU vs CPU parity
    - Calibration improvement
    
    Example:
        >>> validator = InferenceValidator(engine)
        >>> result = validator.validate_all()
        >>> print(result.passed)
    """
    
    def __init__(
        self,
        engine: Any,  # InferenceEngine
        tolerance: float = 1e-5,
    ) -> None:
        """
        Initialize validator.
        
        Args:
            engine: InferenceEngine to validate
            tolerance: Numerical tolerance for comparisons
        """
        self.engine = engine
        self.tolerance = tolerance
    
    def validate_all(self) -> ValidationResult:
        """Run all validations."""
        result = ValidationResult()
        
        # Shape validation
        shape_result = self.validate_shape()
        result.checks.update(shape_result.checks)
        result.errors.extend(shape_result.errors)
        
        # Numerical stability
        stability_result = self.validate_numerical_stability()
        result.checks.update(stability_result.checks)
        result.errors.extend(stability_result.errors)
        
        # Latency
        latency_result = self.validate_latency()
        result.checks.update(latency_result.checks)
        result.metrics.update(latency_result.metrics)
        
        # Determinism
        determinism_result = self.validate_determinism()
        result.checks.update(determinism_result.checks)
        result.errors.extend(determinism_result.errors)
        
        result.passed = all(result.checks.values())
        return result
    
    def validate_shape(self) -> ValidationResult:
        """Validate input/output shapes."""
        result = ValidationResult()
        
        input_shape = self.engine.input_shape
        num_classes = self.engine.num_classes
        
        # Create test input
        test_input = np.random.rand(*input_shape).astype(np.float32)
        
        # Get prediction
        inference_result = self.engine.predict(test_input)
        
        # Check output shape
        probs = inference_result.prediction.probabilities
        expected_shape = (num_classes,)
        
        shape_match = probs.shape == expected_shape
        result.add_check(
            "output_shape",
            shape_match,
            f"Expected {expected_shape}, got {probs.shape}",
        )
        
        # Check probability sum
        prob_sum = np.sum(probs)
        sum_valid = np.isclose(prob_sum, 1.0, atol=1e-3)
        result.add_check(
            "probability_sum",
            sum_valid,
            f"Probabilities sum to {prob_sum}, expected 1.0",
        )
        
        return result
    
    def validate_numerical_stability(self) -> ValidationResult:
        """Validate numerical stability."""
        result = ValidationResult()
        
        input_shape = self.engine.input_shape
        
        # Test with edge cases
        test_cases = {
            "zeros": np.zeros(input_shape, dtype=np.float32),
            "ones": np.ones(input_shape, dtype=np.float32),
            "random": np.random.rand(*input_shape).astype(np.float32),
            "high_values": np.full(input_shape, 255.0, dtype=np.float32),
        }
        
        for name, test_input in test_cases.items():
            try:
                inference_result = self.engine.predict(test_input)
                probs = inference_result.prediction.probabilities
                
                # Check for NaN/Inf
                has_nan = np.isnan(probs).any()
                has_inf = np.isinf(probs).any()
                
                result.add_check(
                    f"no_nan_{name}",
                    not has_nan,
                    f"NaN detected in output for {name} input",
                )
                result.add_check(
                    f"no_inf_{name}",
                    not has_inf,
                    f"Inf detected in output for {name} input",
                )
                
                # Check probability range
                valid_range = (probs >= 0).all() and (probs <= 1).all()
                result.add_check(
                    f"valid_range_{name}",
                    valid_range,
                    f"Probabilities outside [0,1] for {name} input",
                )
                
            except Exception as e:
                result.add_check(
                    f"inference_{name}",
                    False,
                    f"Exception during inference: {e}",
                )
        
        return result
    
    def validate_latency(
        self,
        batch_sizes: list[int] | None = None,
        n_warmup: int = 3,
        n_runs: int = 10,
    ) -> ValidationResult:
        """
        Validate latency performance.
        
        Args:
            batch_sizes: Batch sizes to test
            n_warmup: Number of warm-up runs
            n_runs: Number of timed runs
        
        Returns:
            ValidationResult with latency metrics
        """
        result = ValidationResult()
        
        if batch_sizes is None:
            batch_sizes = [1, 8, 16]
        
        input_shape = self.engine.input_shape
        
        for batch_size in batch_sizes:
            test_input = np.random.rand(batch_size, *input_shape).astype(np.float32)
            
            # Warm up
            for _ in range(n_warmup):
                _ = self.engine.model.predict(test_input, verbose=0)
            
            # Timed runs
            latencies = []
            for _ in range(n_runs):
                start = time.perf_counter()
                _ = self.engine.model.predict(test_input, verbose=0)
                latencies.append((time.perf_counter() - start) * 1000)
            
            avg_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            per_image = avg_latency / batch_size
            
            result.metrics[f"latency_batch_{batch_size}_ms"] = avg_latency
            result.metrics[f"latency_per_image_batch_{batch_size}_ms"] = per_image
            result.metrics[f"latency_std_batch_{batch_size}_ms"] = std_latency
            
            # Check latency is reasonable (< 1 second per image)
            result.add_check(
                f"latency_batch_{batch_size}",
                per_image < 1000,
                f"Latency too high: {per_image:.2f}ms/image",
            )
            
            logger.info(
                f"Batch {batch_size}: {avg_latency:.2f}ms "
                f"({per_image:.2f}ms/image)"
            )
        
        return result
    
    def validate_determinism(self, n_runs: int = 5) -> ValidationResult:
        """Validate deterministic outputs."""
        result = ValidationResult()
        
        input_shape = self.engine.input_shape
        test_input = np.random.rand(*input_shape).astype(np.float32)
        
        # Run multiple times
        outputs = []
        for _ in range(n_runs):
            inference_result = self.engine.predict(test_input)
            outputs.append(inference_result.prediction.probabilities)
        
        # Check all outputs are identical
        reference = outputs[0]
        all_match = all(
            np.allclose(output, reference, atol=self.tolerance)
            for output in outputs[1:]
        )
        
        result.add_check(
            "determinism",
            all_match,
            "Outputs differ across runs for same input",
        )
        
        return result
    
    def validate_gpu_cpu_parity(self) -> ValidationResult:
        """Validate GPU and CPU produce same results."""
        result = ValidationResult()
        
        if not HAS_TF:
            result.add_warning("TensorFlow not available, skipping GPU/CPU parity")
            return result
        
        # Check if GPU is available
        gpus = tf.config.list_physical_devices("GPU")
        if not gpus:
            result.add_warning("No GPU available, skipping parity check")
            result.checks["gpu_cpu_parity"] = True
            return result
        
        input_shape = self.engine.input_shape
        test_input = np.random.rand(*input_shape).astype(np.float32)
        batch = np.expand_dims(test_input, axis=0)
        
        # GPU prediction
        with tf.device("/GPU:0"):
            gpu_output = self.engine.model.predict(batch, verbose=0)
        
        # CPU prediction
        with tf.device("/CPU:0"):
            cpu_output = self.engine.model.predict(batch, verbose=0)
        
        # Compare
        outputs_match = np.allclose(gpu_output, cpu_output, atol=1e-4)
        max_diff = np.max(np.abs(gpu_output - cpu_output))
        
        result.add_check(
            "gpu_cpu_parity",
            outputs_match,
            f"GPU/CPU outputs differ by max {max_diff:.6f}",
        )
        result.metrics["gpu_cpu_max_diff"] = float(max_diff)
        
        return result
    
    def validate_calibration(
        self,
        logits: NDArray[np.float32],
        labels: NDArray[np.int64],
    ) -> ValidationResult:
        """
        Validate calibration improvement.
        
        Args:
            logits: Model logits
            labels: True labels
        
        Returns:
            ValidationResult with calibration metrics
        """
        from ml.inference.calibration import TemperatureScaler
        
        result = ValidationResult()
        
        scaler = TemperatureScaler()
        cal_result = scaler.fit(logits, labels)
        
        result.metrics["ece_before"] = cal_result.ece_before
        result.metrics["ece_after"] = cal_result.ece_after
        result.metrics["optimal_temperature"] = cal_result.temperature
        
        # Check that calibration improved ECE
        improved = cal_result.ece_after <= cal_result.ece_before
        result.add_check(
            "calibration_improvement",
            improved,
            f"ECE increased from {cal_result.ece_before:.4f} to {cal_result.ece_after:.4f}",
        )
        
        logger.info(
            f"Calibration: ECE {cal_result.ece_before:.4f} → {cal_result.ece_after:.4f} "
            f"(T={cal_result.temperature:.3f})"
        )
        
        return result
