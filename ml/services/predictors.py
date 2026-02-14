"""
Predictors for ML Phase 3

Animal predictor uses real TensorFlow model.
Others remain as stub predictors.
"""

import logging
import numpy as np
from ml.contracts.inference import PredictionResult
from ml.runtime.loader import load_animal_model
from ml.registry.class_maps import ANIMAL_CLASSES
from ml.registry.datasets_adapter import get_classes_for_domain

logger = logging.getLogger(__name__)


class AnimalPredictor:
    def __init__(self):
        self.model = load_animal_model()
        # Try to get classes from dataset registry, fallback to hardcoded
        self.classes = get_classes_for_domain("animal") or ANIMAL_CLASSES
        logger.info(f"AnimalPredictor initialized with classes: {self.classes}")

    def predict(self, image):
        # Preprocess image
        img = image.resize((224, 224))
        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img) / 255.0
        arr = arr.reshape(1, 224, 224, 3)

        # Predict
        preds = self.model.predict(arr)
        confidence = float(preds.max())

        # Get label
        label_index = int(preds.argmax())
        if isinstance(self.classes, dict):
            label = self.classes.get(label_index, f"class_{label_index}")
        elif isinstance(self.classes, list) and label_index < len(self.classes):
            label = self.classes[label_index]
        else:
            label = f"class_{label_index}"

        return PredictionResult(label=label, confidence=confidence)


class PlantPredictor:
    def predict(self, image):
        return PredictionResult(label="plant", confidence=0.60)


class HumanPredictor:
    def predict(self, image):
        return PredictionResult(label="human", confidence=0.60)


class MedicalPredictor:
    def predict(self, image):
        return PredictionResult(label="medical", confidence=0.60)
