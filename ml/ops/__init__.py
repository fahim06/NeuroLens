"""
ML Ops Module.

Provides MLOps automation for the NeuroLens platform:
- Validation gates for model promotion
- Retraining triggers for automated training
- Artifact management
- Experiment tracking
"""

from ml.ops.validation_gates import (
    GateResult,
    GateSeverity,
    GateStatus,
    ValidationGate,
    ValidationPipeline,
    ValidationReport,
    MetricThresholdGate,
    RegressionGate,
    LatencyGate,
    CalibrationGate,
    ReproducibilityGate,
    SanityTestGate,
    create_default_pipeline,
)

from ml.ops.retraining_triggers import (
    TriggerEvent,
    TriggerPriority,
    TriggerType,
    RetrainingTrigger,
    TriggerManager,
    DataVersionTrigger,
    DriftTrigger,
    ScheduledTrigger,
    ManualTrigger,
    PerformanceDegradationTrigger,
    create_default_trigger_manager,
)

__all__ = [
    # Validation Gates
    "GateResult",
    "GateSeverity",
    "GateStatus",
    "ValidationGate",
    "ValidationPipeline",
    "ValidationReport",
    "MetricThresholdGate",
    "RegressionGate",
    "LatencyGate",
    "CalibrationGate",
    "ReproducibilityGate",
    "SanityTestGate",
    "create_default_pipeline",
    # Retraining Triggers
    "TriggerEvent",
    "TriggerPriority",
    "TriggerType",
    "RetrainingTrigger",
    "TriggerManager",
    "DataVersionTrigger",
    "DriftTrigger",
    "ScheduledTrigger",
    "ManualTrigger",
    "PerformanceDegradationTrigger",
    "create_default_trigger_manager",
]
