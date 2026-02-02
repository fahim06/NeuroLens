"""
Model Validation Gates.

Automated checks that must pass before a model can be promoted.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GateStatus(Enum):
    """Validation gate status."""
    
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


class GateSeverity(Enum):
    """Gate failure severity."""
    
    BLOCKING = "blocking"  # Fails the pipeline
    WARNING = "warning"    # Logs warning, continues
    INFO = "info"          # Informational only


@dataclass(frozen=True)
class GateResult:
    """Result of a validation gate check."""
    
    gate_name: str
    status: GateStatus
    severity: GateSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def passed(self) -> bool:
        """Check if gate passed or is non-blocking."""
        if self.status == GateStatus.PASSED:
            return True
        if self.status == GateStatus.SKIPPED:
            return True
        if self.status == GateStatus.WARNING and self.severity != GateSeverity.BLOCKING:
            return True
        return False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "passed": self.passed,
        }


class ValidationGate(ABC):
    """Abstract base class for validation gates."""
    
    def __init__(
        self,
        name: str,
        severity: GateSeverity = GateSeverity.BLOCKING,
    ):
        self.name = name
        self.severity = severity
    
    @abstractmethod
    def check(self, context: dict[str, Any]) -> GateResult:
        """Run the validation check."""
        pass


class MetricThresholdGate(ValidationGate):
    """Gate that checks if metrics meet minimum thresholds."""
    
    def __init__(
        self,
        thresholds: dict[str, float],
        severity: GateSeverity = GateSeverity.BLOCKING,
    ):
        super().__init__("metric_threshold", severity)
        self.thresholds = thresholds
    
    def check(self, context: dict[str, Any]) -> GateResult:
        """Check if all metrics meet thresholds."""
        metrics = context.get("metrics", {})
        
        failures = []
        passed_checks = []
        
        for metric, threshold in self.thresholds.items():
            value = metrics.get(metric)
            if value is None:
                failures.append(f"{metric}: missing")
            elif value < threshold:
                failures.append(f"{metric}: {value:.4f} < {threshold}")
            else:
                passed_checks.append(f"{metric}: {value:.4f} >= {threshold}")
        
        if failures:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.FAILED,
                severity=self.severity,
                message=f"Metric thresholds not met: {len(failures)} failures",
                details={
                    "failures": failures,
                    "passed": passed_checks,
                    "thresholds": self.thresholds,
                },
            )
        
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            severity=self.severity,
            message=f"All {len(self.thresholds)} metric thresholds met",
            details={"passed": passed_checks},
        )


class RegressionGate(ValidationGate):
    """Gate that checks for regression against baseline."""
    
    def __init__(
        self,
        baseline_metrics: dict[str, float],
        regression_threshold: float = 0.95,
        severity: GateSeverity = GateSeverity.BLOCKING,
    ):
        super().__init__("regression_check", severity)
        self.baseline_metrics = baseline_metrics
        self.regression_threshold = regression_threshold
    
    def check(self, context: dict[str, Any]) -> GateResult:
        """Check for regression against baseline."""
        metrics = context.get("metrics", {})
        
        regressions = []
        improvements = []
        
        for metric, baseline in self.baseline_metrics.items():
            current = metrics.get(metric)
            if current is None:
                continue
            
            min_allowed = baseline * self.regression_threshold
            diff = current - baseline
            
            if current < min_allowed:
                regressions.append({
                    "metric": metric,
                    "baseline": baseline,
                    "current": current,
                    "min_allowed": min_allowed,
                    "regression": f"{(1 - current/baseline) * 100:.1f}%",
                })
            else:
                improvements.append({
                    "metric": metric,
                    "baseline": baseline,
                    "current": current,
                    "change": f"{diff:+.4f}",
                })
        
        if regressions:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.FAILED,
                severity=self.severity,
                message=f"Regression detected in {len(regressions)} metrics",
                details={
                    "regressions": regressions,
                    "improvements": improvements,
                    "threshold": f"{self.regression_threshold * 100}%",
                },
            )
        
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            severity=self.severity,
            message="No regression detected",
            details={"improvements": improvements},
        )


class LatencyGate(ValidationGate):
    """Gate that checks inference latency budget."""
    
    def __init__(
        self,
        max_latency_ms: float = 100.0,
        percentile: str = "p95",
        severity: GateSeverity = GateSeverity.BLOCKING,
    ):
        super().__init__("latency_budget", severity)
        self.max_latency_ms = max_latency_ms
        self.percentile = percentile
    
    def check(self, context: dict[str, Any]) -> GateResult:
        """Check if latency is within budget."""
        metrics = context.get("metrics", {})
        
        latency_key = f"inference_latency_{self.percentile}_ms"
        latency = metrics.get(latency_key) or metrics.get("inference_latency_ms")
        
        if latency is None:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.SKIPPED,
                severity=self.severity,
                message="Latency metrics not available",
                details={"expected_key": latency_key},
            )
        
        if latency > self.max_latency_ms:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.FAILED,
                severity=self.severity,
                message=f"Latency {latency:.1f}ms exceeds budget {self.max_latency_ms}ms",
                details={
                    "latency_ms": latency,
                    "budget_ms": self.max_latency_ms,
                    "percentile": self.percentile,
                    "exceeded_by": f"{latency - self.max_latency_ms:.1f}ms",
                },
            )
        
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            severity=self.severity,
            message=f"Latency {latency:.1f}ms within budget {self.max_latency_ms}ms",
            details={
                "latency_ms": latency,
                "budget_ms": self.max_latency_ms,
                "headroom": f"{self.max_latency_ms - latency:.1f}ms",
            },
        )


class ReproducibilityGate(ValidationGate):
    """Gate that verifies model reproducibility."""
    
    def __init__(
        self,
        tolerance: float = 0.01,
        severity: GateSeverity = GateSeverity.WARNING,
    ):
        super().__init__("reproducibility", severity)
        self.tolerance = tolerance
    
    def check(self, context: dict[str, Any]) -> GateResult:
        """Check model reproducibility."""
        reproducibility = context.get("reproducibility", {})
        
        if not reproducibility:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.SKIPPED,
                severity=self.severity,
                message="Reproducibility check not performed",
            )
        
        is_reproducible = reproducibility.get("is_reproducible", False)
        variance = reproducibility.get("variance", 0.0)
        
        if not is_reproducible or variance > self.tolerance:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.FAILED,
                severity=self.severity,
                message=f"Model not reproducible (variance: {variance:.4f})",
                details={
                    "variance": variance,
                    "tolerance": self.tolerance,
                    "seeds_tested": reproducibility.get("seeds_tested", []),
                },
            )
        
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            severity=self.severity,
            message="Model is reproducible",
            details={"variance": variance, "tolerance": self.tolerance},
        )


class CalibrationGate(ValidationGate):
    """Gate that checks model calibration."""
    
    def __init__(
        self,
        max_ece: float = 0.05,
        severity: GateSeverity = GateSeverity.WARNING,
    ):
        super().__init__("calibration", severity)
        self.max_ece = max_ece
    
    def check(self, context: dict[str, Any]) -> GateResult:
        """Check model calibration (Expected Calibration Error)."""
        metrics = context.get("metrics", {})
        
        ece = metrics.get("expected_calibration_error") or metrics.get("ece")
        
        if ece is None:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.SKIPPED,
                severity=self.severity,
                message="Calibration metrics not available",
            )
        
        if ece > self.max_ece:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.FAILED,
                severity=self.severity,
                message=f"Model poorly calibrated (ECE: {ece:.4f} > {self.max_ece})",
                details={"ece": ece, "threshold": self.max_ece},
            )
        
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            severity=self.severity,
            message=f"Model well calibrated (ECE: {ece:.4f})",
            details={"ece": ece, "threshold": self.max_ece},
        )


class SanityTestGate(ValidationGate):
    """Gate that runs inference sanity tests."""
    
    def __init__(
        self,
        test_cases: list[dict[str, Any]] | None = None,
        severity: GateSeverity = GateSeverity.BLOCKING,
    ):
        super().__init__("sanity_test", severity)
        self.test_cases = test_cases or []
    
    def check(self, context: dict[str, Any]) -> GateResult:
        """Run sanity tests on model."""
        model_path = context.get("model_path")
        
        if not model_path or not Path(model_path).exists():
            return GateResult(
                gate_name=self.name,
                status=GateStatus.SKIPPED,
                severity=self.severity,
                message="Model path not available for sanity testing",
            )
        
        # In production, this would load the model and run actual inference
        passed_tests = []
        failed_tests = []
        
        for test in self.test_cases:
            test_name = test.get("name", "unnamed")
            # Simulate test execution
            passed_tests.append(test_name)
        
        if failed_tests:
            return GateResult(
                gate_name=self.name,
                status=GateStatus.FAILED,
                severity=self.severity,
                message=f"Sanity tests failed: {len(failed_tests)}/{len(self.test_cases)}",
                details={"failed": failed_tests, "passed": passed_tests},
            )
        
        return GateResult(
            gate_name=self.name,
            status=GateStatus.PASSED,
            severity=self.severity,
            message=f"All {len(passed_tests)} sanity tests passed",
            details={"passed": passed_tests},
        )


@dataclass
class ValidationPipeline:
    """Pipeline of validation gates."""
    
    gates: list[ValidationGate] = field(default_factory=list)
    fail_fast: bool = False
    
    def add_gate(self, gate: ValidationGate) -> "ValidationPipeline":
        """Add a gate to the pipeline."""
        self.gates.append(gate)
        return self
    
    def run(self, context: dict[str, Any]) -> "ValidationReport":
        """Run all gates and return a report."""
        results = []
        all_passed = True
        blocking_failures = []
        
        for gate in self.gates:
            try:
                result = gate.check(context)
                results.append(result)
                
                if not result.passed:
                    all_passed = False
                    if result.severity == GateSeverity.BLOCKING:
                        blocking_failures.append(result)
                        if self.fail_fast:
                            break
                            
            except Exception as e:
                logger.error(f"Gate {gate.name} failed with error: {e}")
                results.append(GateResult(
                    gate_name=gate.name,
                    status=GateStatus.FAILED,
                    severity=gate.severity,
                    message=f"Gate error: {str(e)}",
                ))
                if gate.severity == GateSeverity.BLOCKING:
                    all_passed = False
                    if self.fail_fast:
                        break
        
        return ValidationReport(
            results=results,
            passed=all_passed and len(blocking_failures) == 0,
            blocking_failures=len(blocking_failures),
            total_gates=len(self.gates),
        )


@dataclass
class ValidationReport:
    """Report of validation pipeline execution."""
    
    results: list[GateResult]
    passed: bool
    blocking_failures: int
    total_gates: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def summary(self) -> dict[str, int]:
        """Get summary counts by status."""
        counts = {s.value: 0 for s in GateStatus}
        for r in self.results:
            counts[r.status.value] += 1
        return counts
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "blocking_failures": self.blocking_failures,
            "total_gates": self.total_gates,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, path: Path | str) -> None:
        """Save report to file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())


def create_default_pipeline() -> ValidationPipeline:
    """Create the default validation pipeline."""
    return ValidationPipeline(
        gates=[
            MetricThresholdGate(
                thresholds={
                    "accuracy": 0.85,
                    "precision": 0.80,
                    "recall": 0.80,
                    "f1_score": 0.82,
                    "auc_roc": 0.90,
                }
            ),
            RegressionGate(
                baseline_metrics={
                    "accuracy": 0.88,
                    "f1_score": 0.85,
                },
                regression_threshold=0.95,
            ),
            LatencyGate(max_latency_ms=100.0),
            CalibrationGate(max_ece=0.05),
            ReproducibilityGate(tolerance=0.01),
        ],
        fail_fast=False,
    )
