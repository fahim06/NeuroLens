"""
ML Views — API Endpoints

Django REST API views for ML inference.
Phase 0: Basic structure, no actual inference logic yet.
"""

import logging
import base64
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings

from ml.services.domain_detector import domain_detector_service

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def detect_domain(request):
    """
    Auto-detect the domain of an uploaded image.

    POST /api/ml/detect-domain/
    Body: {'image': <base64_encoded_image>}
    """
    try:
        image_b64 = request.data.get("image")
        if not image_b64:
            return Response(
                {"error": "No image provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decode base64
        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return Response(
                {"error": "Invalid image format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Detect domain
        result = domain_detector_service.detect(image_bytes)

        return Response(
            {
                "domain": result.domain.value,
                "confidence": result.confidence,
                "meta": result.meta,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Domain detection error: {e}")
        return Response(
            {"error": "Domain detection failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def predict(request):
    """
    Run ML prediction on an uploaded image.

    POST /api/ml/predict/
    Body: {
        'image': <base64_encoded_image>,
        'detection_type': 'human_animal' | 'animal_category' | etc.
    }
    """
    try:
        # Phase 0: Return placeholder response
        detection_type = request.data.get("detection_type", "unknown")

        return Response(
            {
                "detection_type": detection_type,
                "prediction": "placeholder",
                "confidence": 0.0,
                "message": "ML prediction not implemented in Phase 0",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return Response(
            {"error": "Prediction failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    ML system health check.

    GET /api/ml/health/
    """
    return Response(
        {
            "status": "healthy",
            "version": getattr(settings, "NEUROLENS_VERSION", "unknown"),
            "phase": "Phase 0 - Architecture Only",
            "models_loaded": 0,
            "message": "ML system initialized but no models loaded yet",
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available_models(request):
    """
    List available ML models.

    GET /api/ml/models/
    """
    # Phase 0: Return empty list
    return Response({"models": [], "message": "No models available in Phase 0"})
