"""
ML Views — API Endpoints

Django REST API views for ML inference.
Phase 0: Basic structure, no actual inference logic yet.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings

from ml.services.domain_detector import domain_detector_service
from ml.services.model_router import model_router
from ml.services.inference_service import inference_service

logger = logging.getLogger(__name__)


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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inference(request):
    """
    Unified inference endpoint — production-ready ML API.

    POST /api/ml/inference/
    Multipart form upload: {'image': <image_file>}
    """
    try:
        # Validate image file
        if "image" not in request.FILES:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_file = request.FILES["image"]

        # Validate file type
        if not image_file.content_type.startswith("image/"):
            return Response(
                {"error": "File must be an image"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if image_file.size > max_size:
            return Response(
                {"error": "Image file too large (max 10MB)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Convert to PIL Image
        from PIL import Image
        from io import BytesIO

        try:
            image = Image.open(BytesIO(image_file.read()))
            # Convert to RGB if necessary
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return Response(
                {"error": "Invalid image file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Run inference
        result = inference_service.infer(image)

        # Check for errors
        if "error" in result:
            # Determine appropriate HTTP status code
            error_detail = result.get("detail", "")
            if "Invalid image" in error_detail or "No image" in error_detail:
                status_code = status.HTTP_400_BAD_REQUEST
            elif "processing failed" in error_detail:
                status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            else:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response(result, status=status_code)

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Inference endpoint error: {e}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
