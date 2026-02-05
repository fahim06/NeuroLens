"""
Brain Tumor Detector Model

Medical image classification for brain tumor detection.
Based on: https://github.com/fahim06/Brain_Tumor

Architecture: VGG16 transfer learning
- Input: 256x256x3 RGB images
- Output: Binary (No Tumor / Tumor)
- Accuracy: 95.21% (VGG16 model)
"""

from typing import Any, Dict

import numpy as np

from ml.registry import DetectionType, model_registry


class BrainTumorDetector:
    """
    Detector for brain tumor classification from MRI images.

    Model Details (from fahim06/Brain_Tumor):
    - VGG16 architecture with custom dense layers
    - Input size: 256x256x3
    - Binary classification: No Tumor (0) vs Tumor (1)
    - Training: 3090 images, Testing: 815 images
    - Performance: 95.21% accuracy, 90.53% precision, 91.85% F1-score
    """

    def __init__(self):
        self.detection_type = DetectionType.BRAIN_TUMOR
        self.config = model_registry.get_config(self.detection_type)
        self._model = None

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for VGG16 model.

        From Brain_Tumor notebooks:
        - Resize to 256x256x3
        - Normalize to [0, 1]
        """
        from PIL import Image

        # Ensure correct shape
        if len(image.shape) == 3:
            image = np.expand_dims(image, axis=0)

        # Normalize to [0, 1] as done in the notebooks
        if image.max() > 1.0:
            image = image.astype("float32") / 255.0

        return image

    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Predict brain tumor presence.

        Args:
            image: Preprocessed numpy array (256x256x3)

        Returns:
            Prediction result with tumor/no tumor classification
        """
        self._model = model_registry.load_model(self.detection_type)

        if self._model is None:
            return self._mock_predict()

        # Preprocess
        processed = self.preprocess(image)

        # Run prediction (from notebooks: np.argmax(model.predict(X), axis=-1))
        predictions = self._model.predict(processed)
        predicted_idx = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][predicted_idx])

        return self._format_result(predicted_idx, confidence, predictions[0])

    def _format_result(
        self, predicted_idx: int, confidence: float, all_probs: np.ndarray
    ) -> Dict[str, Any]:
        """Format prediction result with medical-safe labels."""
        labels = self.config.class_labels

        result = {
            "predicted_class": labels[predicted_idx],
            "confidence": round(confidence, 4),
            "is_tumor": predicted_idx == 1,
            "medical_note": self._get_medical_note(predicted_idx, confidence),
            "all_classes": [
                {"label": labels[i], "confidence": round(float(all_probs[i]), 4)}
                for i in range(len(labels))
            ],
        }

        return result

    def _get_medical_note(self, predicted_idx: int, confidence: float) -> str:
        """Generate medical-safe advisory note."""
        if predicted_idx == 0:  # No Tumor
            if confidence > 0.90:
                return (
                    "No tumor indicators detected. Consult physician for confirmation."
                )
            else:
                return "Low tumor probability. Additional imaging may be recommended."
        else:  # Tumor
            if confidence > 0.90:
                return (
                    "Potential tumor detected. Urgent medical consultation recommended."
                )
            else:
                return "Possible tumor indicators. Further diagnostic imaging advised."

    def _mock_predict(self) -> Dict[str, Any]:
        """Generate mock brain tumor prediction."""
        import random

        confidence = random.uniform(0.80, 0.98)
        # Bias towards "No Tumor" for safer mock results
        predicted_idx = 0 if random.random() > 0.3 else 1

        labels = self.config.class_labels
        if predicted_idx == 0:
            probs = [confidence, 1 - confidence]
        else:
            probs = [1 - confidence, confidence]

        return {
            "predicted_class": labels[predicted_idx],
            "confidence": round(confidence, 4),
            "is_tumor": predicted_idx == 1,
            "medical_note": self._get_medical_note(predicted_idx, confidence),
            "is_mock": True,
            "all_classes": [
                {"label": labels[i], "confidence": round(probs[i], 4)}
                for i in range(len(labels))
            ],
        }
