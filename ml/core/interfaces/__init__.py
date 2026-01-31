"""
ML Interface Contracts

Abstract base classes and protocols defining the contract for all ML components.
"""

from ml.core.interfaces.evaluator import BaseEvaluator
from ml.core.interfaces.model import BaseModel, ModelMetadata
from ml.core.interfaces.preprocessor import BasePreprocessor
from ml.core.interfaces.trainer import BaseTrainer, TrainingConfig

__all__ = [
    "BaseModel",
    "ModelMetadata",
    "BasePreprocessor",
    "BaseTrainer",
    "TrainingConfig",
    "BaseEvaluator",
]
