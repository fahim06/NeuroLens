"""
Celery Tasks for Inference.

This module contains async tasks for ML inference processing.
Tasks are executed by Celery workers in the background.
"""

import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="inference.tasks.run_inference",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=240,
    time_limit=300,
)
def run_inference(self, request_id: str, payload: dict) -> dict:
    """
    Async task to run ML inference.

    Args:
        request_id: UUID of the InferenceRequest
        payload: Dict containing image_data or image_url

    Returns:
        Dict with prediction results
    """
    from inference.models import InferenceRequest
    from inference.services.predictor import PredictorService

    logger.info(f"Starting inference task for request {request_id}")

    try:
        # Get the inference request
        inference_request = InferenceRequest.objects.get(id=request_id)

        # Update status to processing
        inference_request.status = "processing"
        inference_request.started_at = timezone.now()
        inference_request.celery_task_id = self.request.id
        inference_request.save()

        logger.info(f"Processing inference request {request_id}")

        # Run prediction
        from inference.services.predictor import PredictorService

        predictor = PredictorService()
        result = predictor.predict(payload)

        # Update request with result
        inference_request.status = "success"
        inference_request.result = result
        inference_request.completed_at = timezone.now()
        inference_request.save()

        logger.info(f"Inference completed for request {request_id}")

        return result

    except InferenceRequest.DoesNotExist:
        logger.error(f"Inference request {request_id} not found")
        return {"error": "Request not found", "request_id": request_id}

    except SoftTimeLimitExceeded:
        logger.error(f"Inference task timed out for request {request_id}")
        try:
            inference_request = InferenceRequest.objects.get(id=request_id)
            inference_request.status = "failed"
            inference_request.error_message = "Task timed out"
            inference_request.completed_at = timezone.now()
            inference_request.save()
        except Exception:
            pass
        raise

    except Exception as exc:
        logger.exception(f"Inference failed for request {request_id}: {exc}")

        try:
            inference_request = InferenceRequest.objects.get(id=request_id)
            inference_request.status = "failed"
            inference_request.error_message = str(exc)[:500]  # Limit error message
            inference_request.completed_at = timezone.now()
            inference_request.save()
        except Exception:
            pass

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying inference task for request {request_id}")
            raise self.retry(exc=exc)

        return {"error": str(exc), "request_id": request_id}


@shared_task(name="inference.tasks.cleanup_old_requests")
def cleanup_old_requests(days: int = 30) -> dict:
    """
    Cleanup inference requests older than specified days.

    Args:
        days: Number of days to keep requests

    Returns:
        Dict with cleanup statistics
    """
    from inference.models import InferenceRequest
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=days)
    old_requests = InferenceRequest.objects.filter(created_at__lt=cutoff)
    count = old_requests.count()
    old_requests.delete()

    logger.info(f"Cleaned up {count} inference requests older than {days} days")

    return {"deleted": count, "cutoff_days": days}
