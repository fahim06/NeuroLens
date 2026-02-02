"""
Predictor Service — ML Inference Interface

This service provides the interface for ML predictions.
It bridges the Django API layer with the ML runtime.

IMPORTANT: This file should contain NO TensorFlow/ML imports directly.
All ML code is accessed through the ml.runtime module.
"""
import logging
from datetime import datetime
from typing import Any, Dict
import random

logger = logging.getLogger(__name__)


class PredictorService:
    """
    Service class for handling prediction requests.
    Abstracts ML implementation from API layer.
    
    This service acts as a bridge between Django views and the ML runtime.
    It handles errors gracefully to ensure API stability.
    """
    
    def __init__(self):
        """Initialize the predictor service."""
        self._ml_predictor = None
        self._ml_available = False
        self._init_error = None
        self._initialize_ml()
    
    def _initialize_ml(self):
        """
        Attempt to initialize the ML runtime.
        Falls back to mock mode if ML is not available.
        """
        try:
            from ml.runtime import ml_predictor
            self._ml_predictor = ml_predictor
            self._ml_available = True
            logger.info("ML runtime initialized successfully")
        except ImportError as e:
            self._init_error = f"ML runtime not available: {e}"
            logger.warning(self._init_error)
            self._ml_available = False
        except Exception as e:
            self._init_error = f"ML initialization failed: {e}"
            logger.error(self._init_error)
            self._ml_available = False
    
    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a prediction based on the input payload.
        
        Args:
            payload: Dictionary containing input data for prediction.
                     Expected keys: 'image_data' or 'image_url'
        
        Returns:
            Dictionary containing prediction results.
        """
        # Validate payload
        if not payload:
            raise ValueError("Empty payload provided")
        
        # Try ML prediction if available
        if self._ml_available and self._ml_predictor:
            try:
                result = self._ml_predictor.predict(payload)
                return result
            except Exception as e:
                logger.error(f"ML prediction failed, falling back to mock: {e}")
                # Fall through to mock prediction
        
        # Fallback to mock prediction
        return self._mock_predict(payload)
    
    def _mock_predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock prediction results.
        Used when ML runtime is not available.
        """
        main_confidence = random.uniform(0.75, 0.98)
        
        return {
            "success": True,
            "model": "mock_model_v1",
            "prediction": {
                "predicted_class": "healthy",
                "confidence": round(main_confidence, 4),
                "all_classes": [
                    {"label": "healthy", "confidence": round(main_confidence, 4)},
                    {"label": "abnormal", "confidence": round(1 - main_confidence, 4)}
                ]
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "model_version": "1.0.0-mock",
                "inference_time_ms": random.randint(50, 200),
                "is_mock": True,
                "reason": self._init_error or "ML runtime not initialized"
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the predictor service is healthy.
        
        Returns:
            Dictionary with service health status.
        """
        if self._ml_available and self._ml_predictor:
            try:
                return self._ml_predictor.health_check()
            except Exception as e:
                logger.error(f"ML health check failed: {e}")
        
        return {
            "status": "degraded" if self._init_error else "healthy",
            "model_loaded": False,
            "is_mock": True,
            "error": self._init_error
        }


# Singleton instance for use across the application
predictor_service = PredictorService()
