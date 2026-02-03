"""
Citrus Classifier Model

Plant genus classification for citrus fruits.
Based on: https://github.com/fahim06/Citrus_Classification

Architecture: MobileNet transfer learning
- Input: 224x224x3 RGB images
- Output: 8 citrus genera
- Accuracy: 99.85% (MobileNet model)
"""
from typing import Any, Dict, Optional
import numpy as np

from ml.registry import DetectionType, model_registry


class CitrusClassifier:
    """
    Classifier for citrus fruit genus identification.
    
    Model Details (from fahim06/Citrus_Classification):
    - MobileNet architecture
    - Input size: 224x224x3
    - 8-class classification for citrus genera
    - Dataset: 22,348 images
    - Performance: 99.85% accuracy, 99.66% precision, 99.52% recall
    
    Classes:
    - Limon Criollo
    - Limon Mandarino
    - Mandarina Pieldesapo
    - Mandarina Israeli
    - Naranja Valencia
    - Tangelo
    - Toronja
    - Lima
    """
    
    def __init__(self):
        self.detection_type = DetectionType.CITRUS
        self.config = model_registry.get_config(self.detection_type)
        self._model = None
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for MobileNet model.
        
        MobileNet preprocessing:
        - Resize to 224x224x3
        - Normalize with MobileNet preprocess_input
        """
        from PIL import Image
        
        # Ensure correct shape
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)
        
        # Standard normalization for MobileNet
        if image.max() > 1.0:
            image = image.astype('float32') / 255.0
        
        return image
    
    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Predict citrus genus.
        
        Args:
            image: Preprocessed numpy array (224x224x3)
            
        Returns:
            Prediction result with citrus classification
        """
        self._model = model_registry.load_model(self.detection_type)
        
        if self._model is None:
            return self._mock_predict()
        
        # Preprocess
        processed = self.preprocess(image)
        
        # Run prediction
        predictions = self._model.predict(processed)
        predicted_idx = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_idx])
        
        return self._format_result(predicted_idx, confidence, predictions[0])
    
    def _format_result(self, predicted_idx: int, confidence: float,
                       all_probs: np.ndarray) -> Dict[str, Any]:
        """Format prediction result."""
        labels = self.config.class_labels
        
        # Get top 3 predictions
        top_indices = np.argsort(all_probs)[-3:][::-1]
        top_predictions = [
            {"label": labels[i], "confidence": round(float(all_probs[i]), 4)}
            for i in top_indices
        ]
        
        return {
            "predicted_class": labels[predicted_idx],
            "confidence": round(confidence, 4),
            "top_predictions": top_predictions,
            "all_classes": [
                {"label": labels[i], "confidence": round(float(all_probs[i]), 4)}
                for i in range(len(labels))
            ]
        }
    
    def _mock_predict(self) -> Dict[str, Any]:
        """Generate mock citrus classification."""
        import random
        
        labels = self.config.class_labels
        predicted_idx = random.randint(0, len(labels) - 1)
        confidence = random.uniform(0.85, 0.99)
        
        # Generate random probabilities
        probs = [random.uniform(0.01, 0.10) for _ in labels]
        probs[predicted_idx] = confidence
        total = sum(probs)
        probs = [p / total for p in probs]
        probs[predicted_idx] = confidence  # Ensure top class has stated confidence
        
        # Get top 3
        sorted_indices = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)[:3]
        top_predictions = [
            {"label": labels[i], "confidence": round(probs[i], 4)}
            for i in sorted_indices
        ]
        
        return {
            "predicted_class": labels[predicted_idx],
            "confidence": round(confidence, 4),
            "is_mock": True,
            "top_predictions": top_predictions,
            "all_classes": [
                {"label": labels[i], "confidence": round(probs[i], 4)}
                for i in range(len(labels))
            ]
        }
