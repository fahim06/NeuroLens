"""
Stub Predictors for Phase 2

These are placeholder predictors that return fixed results.
Real models will be implemented in Phase 3.
"""

from ml.contracts.inference import PredictionResult


class AnimalPredictor:
    def predict(self, image):
        return PredictionResult(label="animal", confidence=0.60)


class PlantPredictor:
    def predict(self, image):
        return PredictionResult(label="plant", confidence=0.60)


class HumanPredictor:
    def predict(self, image):
        return PredictionResult(label="human", confidence=0.60)


class MedicalPredictor:
    def predict(self, image):
        return PredictionResult(label="medical", confidence=0.60)
