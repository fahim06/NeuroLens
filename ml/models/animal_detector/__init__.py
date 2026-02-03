"""
Animal Detector Model

Human vs Animal binary classification.
"""
from typing import Any, Dict, Optional
import numpy as np

from ml.registry import DetectionType, model_registry


class AnimalDetector:
    """Detector for Human vs Animal classification."""
    
    def __init__(self):
        self.detection_type = DetectionType.HUMAN_ANIMAL
        self.config = model_registry.get_config(self.detection_type)
        self._model = None
    
    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Predict whether image contains human or animal.
        
        Args:
            image: Preprocessed numpy array
            
        Returns:
            Prediction result with class and confidence
        """
        self._model = model_registry.load_model(self.detection_type)
        
        if self._model is None:
            # Mock prediction when model not available
            return self._mock_predict()
        
        # Run actual prediction
        predictions = self._model.predict(image)
        predicted_idx = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_idx])
        
        return {
            "predicted_class": self.config.class_labels[predicted_idx],
            "confidence": round(confidence, 4),
            "all_classes": [
                {"label": label, "confidence": round(float(predictions[0][i]), 4)}
                for i, label in enumerate(self.config.class_labels)
            ]
        }
    
    def _mock_predict(self) -> Dict[str, Any]:
        """Generate mock prediction."""
        import random
        confidence = random.uniform(0.75, 0.98)
        predicted_idx = random.choice([0, 1])
        
        return {
            "predicted_class": self.config.class_labels[predicted_idx],
            "confidence": round(confidence, 4),
            "is_mock": True,
            "all_classes": [
                {"label": "Human", "confidence": round(confidence if predicted_idx == 0 else 1 - confidence, 4)},
                {"label": "Animal", "confidence": round(1 - confidence if predicted_idx == 0 else confidence, 4)}
            ]
        }
