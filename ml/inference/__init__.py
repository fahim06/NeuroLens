"""
NeuroLens Inference System

Inference engine for serving trained models reliably and efficiently.

Architecture:
    - loader.py: Model and artifact loading
    - preprocessor.py: Frozen preprocessing pipeline
    - batcher.py: Efficient batching
    - postprocess.py: Output post-processing
    - calibration.py: Confidence calibration
    - explainability/: Grad-CAM and interpretability
    - engine.py: Main inference engine
    - validate.py: Validation suite

Flow:
    Input → Load Frozen Preprocessor → Transform → Batch → Predict → Calibrate → Postprocess → Output

Usage:
    from ml.inference import InferenceEngine
    
    engine = InferenceEngine.from_checkpoint("path/to/model.keras")
    result = engine.predict(image)
    print(result.class_name, result.confidence)
"""

from ml.inference.engine import InferenceEngine, InferenceResult
from ml.inference.loader import ModelLoader, ArtifactBundle
from ml.inference.preprocessor import InferencePreprocessor, PreprocessorConfig
from ml.inference.batcher import InferenceBatcher, BatchConfig
from ml.inference.postprocess import Postprocessor, PredictionOutput
from ml.inference.calibration import TemperatureScaler, CalibrationResult

__all__ = [
    # Engine
    "InferenceEngine",
    "InferenceResult",
    # Loader
    "ModelLoader",
    "ArtifactBundle",
    # Preprocessor
    "InferencePreprocessor",
    "PreprocessorConfig",
    # Batcher
    "InferenceBatcher",
    "BatchConfig",
    # Postprocess
    "Postprocessor",
    "PredictionOutput",
    # Calibration
    "TemperatureScaler",
    "CalibrationResult",
]
