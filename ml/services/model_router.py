# ml/services/model_router.py
"""
Model Router Service.
Routes to appropriate predictor based on detected domain.
"""

import logging
from ml.contracts.domain import PrimaryDomain
from .predictors import (
    AnimalPredictor,
    PlantPredictor,
    HumanPredictor,
    MedicalPredictor,
)

logger = logging.getLogger(__name__)


class ModelRouter:
    def get_predictor(self, domain: PrimaryDomain):
        logger.info(f"Routing to predictor for domain: {domain.value}")
        if domain == PrimaryDomain.ANIMAL:
            return AnimalPredictor()
        if domain == PrimaryDomain.PLANT:
            return PlantPredictor()
        if domain == PrimaryDomain.MEDICAL:
            return MedicalPredictor()
        return HumanPredictor()


model_router = ModelRouter()
