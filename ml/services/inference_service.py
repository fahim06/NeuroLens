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
from ml.errors import MLException

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

            # Structured logging for observability
            logger.info(
                f"[OBSERVABILITY] domain_detected domain={domain} confidence={domain_result.confidence:.2f}"
            )

            # Step 2: Route to predictor
            logger.info(f"Routing to predictor for domain: {domain}")
            predictor = self.model_router.get_predictor(domain_result.domain)
            model_name = predictor.__class__.__name__.replace(
                "Predictor", "_predictor"
            ).lower()
            logger.info(f"Selected model: {model_name}")

            # Structured logging for observability
            logger.info(
                f"[OBSERVABILITY] model_selected model={model_name} domain={domain}"
            )

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

            # Structured logging for observability
            logger.info(
                f"[OBSERVABILITY] inference_completed domain={domain} model={model_name} prediction={prediction_result.label} confidence={prediction_result.confidence:.3f} total_time_ms={processing_time_ms} domain_time_ms={int(domain_time * 1000)} prediction_time_ms={int(prediction_time * 1000)}"
            )
            return response

        except MLException as e:
            logger.error(f"ML error: {e}")
            processing_time_ms = int((time.time() - total_start_time) * 1000)

            # Optional Sentry integration
            try:
                import sentry_sdk

                sentry_sdk.capture_exception(e)
            except ImportError:
                pass  # Sentry not configured

            # Structured logging for observability
            logger.error(
                f"[OBSERVABILITY] inference_failed error_type={type(e).__name__} error_message={str(e)} processing_time_ms={processing_time_ms}"
            )

            return {
                "error": "Inference failed",
                "detail": "Model could not process image",
                "metadata": {
                    "processing_time_ms": processing_time_ms,
                    "error_type": type(e).__name__,
                },
            }

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            processing_time_ms = int((time.time() - total_start_time) * 1000)

            # Optional Sentry integration
            try:
                import sentry_sdk

                sentry_sdk.capture_exception(e)
            except ImportError:
                pass  # Sentry not configured

            # Structured logging for observability
            logger.error(
                f"[OBSERVABILITY] inference_failed error_type={type(e).__name__} error_message={str(e)} processing_time_ms={processing_time_ms}"
            )

            return {
                "error": "Inference failed",
                "detail": "Unexpected error occurred",
                "metadata": {
                    "processing_time_ms": processing_time_ms,
                    "error_type": type(e).__name__,
                },
            }


# Global service instance
inference_service = InferenceService()
