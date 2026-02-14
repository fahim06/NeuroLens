# ml/services/model_router.py
"""
Model Router Service.
Phase 0: Interface only, no actual routing logic.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RoutedPrediction:
    """Result of a routed prediction."""

    def __init__(
        self,
        domain_result: Any,
        prediction: Dict[str, Any],
        model_used: str,
        success: bool,
        error: Optional[str] = None,
    ):
        self.domain_result = domain_result
        self.prediction = prediction
        self.model_used = model_used
        self.success = success
        self.error = error


class ModelRouterService:
    """
    Routes images to appropriate models based on auto-detected domain.

    Phase 0: Interface only, returns placeholder results.
    """

    def __init__(self):
        """Initialize the model router service."""
        logger.info("ModelRouterService initialized (Phase 0)")

    def route_and_predict(
        self, image_data: bytes, detection_type: Optional[str] = None
    ) -> RoutedPrediction:
        """
        Route image to appropriate model and get prediction.

        Args:
            image_data: Raw image bytes
            detection_type: Optional detection type override

        Returns:
            RoutedPrediction with results
        """
        # Phase 0: Return placeholder result
        return RoutedPrediction(
            domain_result=None,
            prediction={
                "prediction": "placeholder",
                "confidence": 0.0,
                "message": "Model routing not implemented in Phase 0",
            },
            model_used="unknown",
            success=False,
            error="Phase 0 - No models available",
        )

    def get_available_models(self) -> Dict[str, Any]:
        """
        Get information about available models.

        Returns:
            Dictionary of model information
        """
        # Phase 0: Return empty dict
        return {}


# Global service instance
model_router_service = ModelRouterService()
