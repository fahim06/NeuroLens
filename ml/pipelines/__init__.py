"""
ML Pipelines Module

Contains training and inference pipelines with strict separation.
"""

from ml.pipelines.preprocess import PreprocessingPipeline
from ml.pipelines.train import TrainingPipeline
from ml.pipelines.infer import InferencePipeline
from ml.pipelines.evaluate import EvaluationPipeline

__all__ = [
    "PreprocessingPipeline",
    "TrainingPipeline",
    "InferencePipeline",
    "EvaluationPipeline",
]
