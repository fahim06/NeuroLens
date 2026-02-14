"""
Predictors for ML Phase 3

Animal predictor uses real TensorFlow model.
Others remain as stub predictors.
"""

import logging
import numpy as np
from ml.contracts.inference import PredictionResult
from ml.runtime.loader import load_animal_model
from ml.runtime.preprocessing import prepare_image
from ml.registry.class_maps import ANIMAL_CLASSES
from ml.registry.datasets_adapter import get_classes_for_domain

logger = logging.getLogger(__name__)


class AnimalPredictor:
    _model = None
    _classes = None

    def __init__(self):
        # Singleton pattern: load model only once
        if AnimalPredictor._model is None:
            AnimalPredictor._model = load_animal_model()
            logger.info("AnimalPredictor model loaded (singleton)")

        # Singleton pattern: load classes only once
        if AnimalPredictor._classes is None:
            AnimalPredictor._classes = (
                get_classes_for_domain("animal") or ANIMAL_CLASSES
            )
            logger.info(f"AnimalPredictor classes loaded: {AnimalPredictor._classes}")

        self.model = AnimalPredictor._model
        self.classes = AnimalPredictor._classes

    def predict(self, image):
        # Use centralized preprocessing
        arr = prepare_image(image)

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
