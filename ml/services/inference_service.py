"""
Inference Service — Unified ML Inference Orchestration

Orchestrates domain detection, model routing, and prediction for unified API.
Phase 5: Production-ready unified inference endpoint.
"""

import logging
import time
from typing import Dict, Any
from PIL import Image

from ml.contracts.inference import InferenceResponse, PredictionResult
from ml.contracts.domain import PrimaryDomain
from ml.services.domain_detector import domain_detector_service
from ml.services.model_router import model_router

logger = logging.getLogger(__name__)


class InferenceService:
    """
    Unified inference service that orchestrates the complete ML pipeline.
    """

    def __init__(self):
        self.domain_detector = domain_detector_service
        self.model_router = model_router

    def infer(self, image: Image.Image) -> Dict[str, Any]:
        """
        Run complete inference pipeline.
        """
        total_start_time = time.time()

        try:
            # Step 1: Detect domain
            logger.info("Starting domain detection")
            domain_start_time = time.time()
            domain_result = self.domain_detector.detect(image)
            domain_time = time.time() - domain_start_time
            domain = domain_result.domain.value
            logger.info(
                f"Domain detection completed in {domain_time:.2f}s: {domain}, confidence: {domain_result.confidence}"
            )

            # Step 2: Route to predictor
            logger.info(f"Routing to predictor for domain: {domain}")
            predictor = self.model_router.get_predictor(domain_result.domain)
            model_name = predictor.__class__.__name__.replace(
                "Predictor", "_predictor"
            ).lower()
            logger.info(f"Selected model: {model_name}")

            # Step 3: Run prediction
            logger.info("Running prediction")
            prediction_start_time = time.time()
            prediction_result = predictor.predict(image)
            prediction_time = time.time() - prediction_start_time
            logger.info(
                f"Prediction completed in {prediction_time:.2f}s: {prediction_result.label} ({prediction_result.confidence:.3f})"
            )

            # Step 4: Calculate processing time
            processing_time_ms = int((time.time() - total_start_time) * 1000)

            # Step 5: Build standardized response
            response = {
                "domain": domain,
                "prediction": prediction_result.label,
                "confidence": prediction_result.confidence,
                "model": model_name,
                "metadata": {
                    "dataset": f"{domain}-v1",
                    "method": "cnn",
                    "processing_time_ms": processing_time_ms,
                    "domain_detection_time_ms": int(domain_time * 1000),
                    "prediction_time_ms": int(prediction_time * 1000),
                    "domain_confidence": domain_result.confidence,
                },
            }

            logger.info(
                f"Inference completed in {processing_time_ms}ms (domain: {int(domain_time * 1000)}ms, prediction: {int(prediction_time * 1000)}ms): {prediction_result.label} ({prediction_result.confidence:.3f})"
            )
            return response

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            processing_time_ms = int((time.time() - total_start_time) * 1000)
            return {
                "error": "Inference failed",
                "domain": "unknown",
                "prediction": "error",
                "confidence": 0.0,
                "model": "error",
                "metadata": {"processing_time_ms": processing_time_ms, "error": str(e)},
            }


# Global service instance
inference_service = InferenceService()
