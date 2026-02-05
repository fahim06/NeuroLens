"""
Multi-Domain Inference Engine

Unified inference interface for all detection types.
Routes requests to appropriate model based on detection_type.

Phase 10: Replaces DR-specific inference with multi-domain support.
"""
import logging
import base64
import io
from datetime import datetime
from typing import Any, Dict, Optional, Union

# Conditional numpy import
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False
    logging.getLogger(__name__).warning("NumPy not available - ML functionality disabled")

from ml.registry import DetectionType, model_registry, DETECTION_CONFIGS

logger = logging.getLogger(__name__)


class MultiDomainInferenceEngine:
    """
    Unified inference engine for multi-domain detection.
    
    Responsibilities:
    - Route requests to appropriate model based on detection_type
    - Handle preprocessing per model requirements
    - Format outputs consistently
    """
    
    def __init__(self):
        """Initialize the inference engine."""
        self._detectors = {}
        logger.info("MultiDomainInferenceEngine initialized")
    
    def predict(self, image_data: Union[str, bytes], 
                detection_type: str) -> Dict[str, Any]:
        """
        Execute prediction for the specified detection type.
        
        Args:
            image_data: Base64 encoded image or raw bytes
            detection_type: One of DetectionType values
            
        Returns:
            Structured prediction result
        """
        # Validate detection type
        try:
            dt = DetectionType(detection_type)
        except ValueError:
            raise ValueError(f"Invalid detection type: {detection_type}. "
                           f"Valid types: {[d.value for d in DetectionType]}")
        
        config = model_registry.get_config(dt)
        
        # Preprocess image
        image = self._preprocess_image(image_data, config.input_size, config.preprocessing)
        
        # Get or create detector
        detector = self._get_detector(dt)
        
        # Run prediction
        start_time = datetime.utcnow()
        prediction = detector.predict(image)
        inference_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Format result
        return {
            "success": True,
            "detection_type": dt.value,
            "detection_name": config.name,
            "prediction": prediction,
            "model_info": {
                "name": config.name,
                "input_size": config.input_size,
                "num_classes": config.num_classes,
                "output_format": config.output_format
            },
            "timestamp": datetime.utcnow().isoformat(),
            "inference_time_ms": round(inference_time * 1000, 2)
        }
    
    def _get_detector(self, detection_type: DetectionType):
        """Get or create detector for the specified type."""
        if detection_type in self._detectors:
            return self._detectors[detection_type]
        
        # Lazy import detectors
        if detection_type == DetectionType.HUMAN_ANIMAL:
            from ml.models.animal_detector import AnimalDetector
            detector = AnimalDetector()
        elif detection_type == DetectionType.ANIMAL_CATEGORY:
            from ml.models.animal_detector import AnimalDetector
            detector = AnimalDetector()  # Reuse for now
        elif detection_type == DetectionType.BIOLOGICAL:
            from ml.models.bio_classifier import BiologicalClassifier
            detector = BiologicalClassifier()
        elif detection_type == DetectionType.BRAIN_TUMOR:
            from ml.models.brain_tumor import BrainTumorDetector
            detector = BrainTumorDetector()
        elif detection_type == DetectionType.CITRUS:
            from ml.models.citrus_classifier import CitrusClassifier
            detector = CitrusClassifier()
        else:
            raise ValueError(f"No detector implemented for {detection_type}")
        
        self._detectors[detection_type] = detector
        return detector
    
    def _preprocess_image(self, image_data: Union[str, bytes], 
                          target_size: tuple,
                          preprocessing: str) -> np.ndarray:
        """
        Preprocess image for model input.
        
        Args:
            image_data: Base64 string or bytes
            target_size: Target dimensions (height, width)
            preprocessing: Preprocessing type ('vgg16', 'mobilenet', 'standard')
            
        Returns:
            Preprocessed numpy array
        """
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for image preprocessing but is not available")
        
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL not available for image preprocessing")
            raise ImportError("Pillow is required for image preprocessing")
        
        # Decode image data
        if isinstance(image_data, str):
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to target dimensions
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(image, dtype=np.float32)
        
        # Apply preprocessing based on type
        if preprocessing == 'vgg16':
            # VGG16 preprocessing: scale to [0, 1]
            img_array = img_array / 255.0
        elif preprocessing == 'mobilenet':
            # MobileNet preprocessing: scale to [0, 1]
            img_array = img_array / 255.0
        else:
            # Standard preprocessing
            img_array = img_array / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def get_available_detection_types(self) -> list:
        """Get list of available detection types for UI."""
        return model_registry.get_available_types()


# Global engine instance
inference_engine = MultiDomainInferenceEngine()
