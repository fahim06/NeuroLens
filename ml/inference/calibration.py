"""
Confidence Calibration

Temperature scaling and calibration metrics for model confidence.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)


@dataclass
class CalibrationResult:
    """
    Calibration result.
    
    Attributes:
        temperature: Optimal temperature
        ece_before: ECE before calibration
        ece_after: ECE after calibration
        reliability_diagram: Binned accuracy vs confidence
    """
    
    temperature: float = 1.0
    ece_before: float = 0.0
    ece_after: float = 0.0
    reliability_diagram: dict[str, list[float]] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "temperature": self.temperature,
            "ece_before": self.ece_before,
            "ece_after": self.ece_after,
            "reliability_diagram": self.reliability_diagram,
        }


class TemperatureScaler:
    """
    Temperature scaling for confidence calibration.
    
    Temperature scaling is a simple post-hoc calibration method that
    scales the logits by a learned temperature parameter.
    
    Higher temperature → softer probabilities (less confident)
    Lower temperature → sharper probabilities (more confident)
    
    Example:
        >>> scaler = TemperatureScaler()
        >>> result = scaler.fit(logits, labels)
        >>> calibrated = scaler.scale(probabilities)
    """
    
    def __init__(
        self,
        n_bins: int = 15,
        initial_temperature: float = 1.0,
    ) -> None:
        """
        Initialize temperature scaler.
        
        Args:
            n_bins: Number of bins for ECE calculation
            initial_temperature: Starting temperature for optimization
        """
        self.n_bins = n_bins
        self.temperature = initial_temperature
        self._fitted = False
    
    def fit(
        self,
        logits: NDArray[np.float32],
        labels: NDArray[np.int64],
        lr: float = 0.01,
        max_iter: int = 100,
    ) -> CalibrationResult:
        """
        Fit optimal temperature using validation data.
        
        Args:
            logits: Model logits (before softmax)
            labels: True labels
            lr: Learning rate for optimization
            max_iter: Maximum iterations
        
        Returns:
            CalibrationResult with optimal temperature
        """
        logger.info("Fitting temperature scaling...")
        
        # Calculate ECE before calibration
        probs_before = self._softmax(logits)
        ece_before = self.expected_calibration_error(probs_before, labels)
        
        # Grid search for optimal temperature
        best_temp = 1.0
        best_ece = ece_before
        
        for temp in np.linspace(0.5, 3.0, 50):
            scaled_logits = logits / temp
            probs = self._softmax(scaled_logits)
            ece = self.expected_calibration_error(probs, labels)
            
            if ece < best_ece:
                best_ece = ece
                best_temp = temp
        
        self.temperature = best_temp
        self._fitted = True
        
        # Calculate ECE after calibration
        probs_after = self._softmax(logits / self.temperature)
        ece_after = self.expected_calibration_error(probs_after, labels)
        
        # Generate reliability diagram
        reliability = self._reliability_diagram(probs_after, labels)
        
        logger.info(
            f"Temperature scaling: T={self.temperature:.3f}, "
            f"ECE: {ece_before:.4f} → {ece_after:.4f}"
        )
        
        return CalibrationResult(
            temperature=self.temperature,
            ece_before=ece_before,
            ece_after=ece_after,
            reliability_diagram=reliability,
        )
    
    def scale(
        self,
        probabilities: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """
        Apply temperature scaling to probabilities.
        
        Args:
            probabilities: Model probabilities
        
        Returns:
            Calibrated probabilities
        """
        if not self._fitted:
            logger.warning("Temperature scaler not fitted, using T=1.0")
            return probabilities
        
        # Convert to logits, scale, convert back
        logits = np.log(probabilities + 1e-10)
        scaled_logits = logits / self.temperature
        return self._softmax(scaled_logits)
    
    def scale_logits(
        self,
        logits: NDArray[np.float32],
    ) -> NDArray[np.float32]:
        """
        Apply temperature scaling to logits.
        
        Args:
            logits: Model logits
        
        Returns:
            Scaled logits
        """
        return logits / self.temperature
    
    def expected_calibration_error(
        self,
        probabilities: NDArray[np.float32],
        labels: NDArray[np.int64],
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).
        
        ECE measures the difference between confidence and accuracy.
        Lower ECE means better calibration.
        
        Args:
            probabilities: Model probabilities
            labels: True labels
        
        Returns:
            ECE value
        """
        confidences = np.max(probabilities, axis=1)
        predictions = np.argmax(probabilities, axis=1)
        accuracies = (predictions == labels).astype(np.float32)
        
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        ece = 0.0
        
        for i in range(self.n_bins):
            in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                avg_confidence = confidences[in_bin].mean()
                avg_accuracy = accuracies[in_bin].mean()
                ece += np.abs(avg_accuracy - avg_confidence) * prop_in_bin
        
        return float(ece)
    
    def _reliability_diagram(
        self,
        probabilities: NDArray[np.float32],
        labels: NDArray[np.int64],
    ) -> dict[str, list[float]]:
        """Generate reliability diagram data."""
        confidences = np.max(probabilities, axis=1)
        predictions = np.argmax(probabilities, axis=1)
        accuracies = (predictions == labels).astype(np.float32)
        
        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2
        
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []
        
        for i in range(self.n_bins):
            in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
            count = in_bin.sum()
            bin_counts.append(int(count))
            
            if count > 0:
                bin_accuracies.append(float(accuracies[in_bin].mean()))
                bin_confidences.append(float(confidences[in_bin].mean()))
            else:
                bin_accuracies.append(0.0)
                bin_confidences.append(float(bin_centers[i]))
        
        return {
            "bin_centers": bin_centers.tolist(),
            "accuracies": bin_accuracies,
            "confidences": bin_confidences,
            "counts": bin_counts,
        }
    
    def _softmax(self, x: NDArray[np.float32]) -> NDArray[np.float32]:
        """Apply softmax."""
        if x.ndim == 1:
            exp_x = np.exp(x - np.max(x))
            return exp_x / exp_x.sum()
        else:
            exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
            return exp_x / exp_x.sum(axis=1, keepdims=True)
    
    def save(self, path: str) -> None:
        """Save temperature to file."""
        import json
        with open(path, "w") as f:
            json.dump({"temperature": self.temperature}, f)
        logger.info(f"Temperature saved to {path}")
    
    def load(self, path: str) -> None:
        """Load temperature from file."""
        import json
        with open(path) as f:
            data = json.load(f)
        self.temperature = data["temperature"]
        self._fitted = True
        logger.info(f"Temperature loaded: {self.temperature}")


class PlattScaler:
    """
    Platt scaling for binary calibration.
    
    Fits a logistic regression on the logits.
    More flexible than temperature scaling but requires more data.
    """
    
    def __init__(self) -> None:
        """Initialize Platt scaler."""
        self.a = 1.0  # Scale parameter
        self.b = 0.0  # Shift parameter
        self._fitted = False
    
    def fit(
        self,
        logits: NDArray[np.float32],
        labels: NDArray[np.int64],
        max_iter: int = 100,
    ) -> CalibrationResult:
        """
        Fit Platt scaling parameters.
        
        Args:
            logits: Model logits (1D for binary)
            labels: True labels
            max_iter: Maximum iterations
        
        Returns:
            CalibrationResult
        """
        # For simplicity, use grid search
        # In production, use scipy.optimize
        
        probs_before = self._sigmoid(logits)
        ece_before = self._ece(probs_before, labels)
        
        best_a, best_b = 1.0, 0.0
        best_ece = ece_before
        
        for a in np.linspace(0.5, 2.0, 20):
            for b in np.linspace(-1.0, 1.0, 20):
                scaled = a * logits + b
                probs = self._sigmoid(scaled)
                ece = self._ece(probs, labels)
                
                if ece < best_ece:
                    best_ece = ece
                    best_a, best_b = a, b
        
        self.a = best_a
        self.b = best_b
        self._fitted = True
        
        probs_after = self._sigmoid(self.a * logits + self.b)
        ece_after = self._ece(probs_after, labels)
        
        return CalibrationResult(
            temperature=self.a,
            ece_before=ece_before,
            ece_after=ece_after,
        )
    
    def scale(self, logits: NDArray[np.float32]) -> NDArray[np.float32]:
        """Apply Platt scaling."""
        return self._sigmoid(self.a * logits + self.b)
    
    def _sigmoid(self, x: NDArray[np.float32]) -> NDArray[np.float32]:
        """Sigmoid function."""
        return 1 / (1 + np.exp(-x))
    
    def _ece(self, probs: NDArray[np.float32], labels: NDArray[np.int64]) -> float:
        """Calculate ECE for binary classification."""
        accuracies = (probs > 0.5).astype(np.int64) == labels
        
        bins = np.linspace(0, 1, 11)
        ece = 0.0
        
        for i in range(10):
            in_bin = (probs > bins[i]) & (probs <= bins[i + 1])
            if in_bin.sum() > 0:
                avg_conf = probs[in_bin].mean()
                avg_acc = accuracies[in_bin].mean()
                ece += np.abs(avg_acc - avg_conf) * in_bin.mean()
        
        return float(ece)
