import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from datasets.models import Dataset
from .models import InferenceRequest
from .serializers import (
    InferenceRequestSerializer,
    PredictRequestSerializer,
)
from .services.predictor import predictor_service

logger = logging.getLogger(__name__)


class PredictView(APIView):
    """
    Handle prediction requests.
    
    POST: Submit an image for prediction (sync mode)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Process a prediction request synchronously.
        
        Accepts image data and returns prediction results.
        """
        logger.info(f"Prediction request from user {request.user.id}")
        
        # Validate input
        serializer = PredictRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid prediction request: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get optional dataset
        dataset = None
        if validated_data.get('dataset_id'):
            try:
                dataset = Dataset.objects.get(pk=validated_data['dataset_id'])
            except Dataset.DoesNotExist:
                pass
        
        # Create inference request record
        inference_request = InferenceRequest.objects.create(
            requested_by=request.user,
            dataset=dataset,
            status=InferenceRequest.Status.PROCESSING,
            started_at=timezone.now(),
            input_data={
                "has_image_data": bool(validated_data.get('image_data')),
                "image_url": validated_data.get('image_url')
            }
        )
        
        logger.info(f"Created inference request {inference_request.id}")
        
        try:
            # Call the predictor service
            prediction_result = predictor_service.predict({
                "image_data": validated_data.get('image_data'),
                "image_url": validated_data.get('image_url')
            })
            
            # Update inference request with results
            inference_request.status = InferenceRequest.Status.SUCCESS
            inference_request.result = prediction_result
            inference_request.completed_at = timezone.now()
            inference_request.save()
            
            # Add request ID to response
            prediction_result['request_id'] = str(inference_request.id)
            
            logger.info(f"Prediction completed for request {inference_request.id}")
            
            return Response(prediction_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Handle prediction failure
            logger.exception(f"Prediction failed for request {inference_request.id}: {e}")
            
            inference_request.status = InferenceRequest.Status.FAILED
            inference_request.error_message = str(e)
            inference_request.completed_at = timezone.now()
            inference_request.save()
            
            return Response(
                {
                    "success": False,
                    "error": str(e),
                    "request_id": str(inference_request.id)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AsyncPredictView(APIView):
    """
    Handle asynchronous prediction requests.
    
    POST: Submit an image for prediction (async mode)
    Returns immediately with request ID, processes in background.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Enqueue a prediction request for async processing.
        
        Returns request ID immediately. Use /api/inference/{id}/status/ to check progress.
        """
        from .tasks import run_inference
        
        logger.info(f"Async prediction request from user {request.user.id}")
        
        # Validate input
        serializer = PredictRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid async prediction request: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        
        # Get optional dataset
        dataset = None
        if validated_data.get('dataset_id'):
            try:
                dataset = Dataset.objects.get(pk=validated_data['dataset_id'])
            except Dataset.DoesNotExist:
                pass
        
        # Create inference request record
        inference_request = InferenceRequest.objects.create(
            requested_by=request.user,
            dataset=dataset,
            status=InferenceRequest.Status.PENDING,
            input_data={
                "has_image_data": bool(validated_data.get('image_data')),
                "image_url": validated_data.get('image_url')
            }
        )
        
        logger.info(f"Created async inference request {inference_request.id}")
        
        # Prepare payload for task
        payload = {
            "image_data": validated_data.get('image_data'),
            "image_url": validated_data.get('image_url')
        }
        
        # Enqueue the task
        try:
            task = run_inference.delay(str(inference_request.id), payload)
            inference_request.celery_task_id = task.id
            inference_request.save()
            
            logger.info(f"Enqueued task {task.id} for request {inference_request.id}")
            
            return Response({
                "success": True,
                "message": "Prediction request queued",
                "request_id": str(inference_request.id),
                "task_id": task.id,
                "status": "pending",
                "status_url": f"/api/inference/{inference_request.id}/status/"
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.exception(f"Failed to enqueue task for request {inference_request.id}: {e}")
            
            # If Redis/Celery is down, fall back to sync processing
            inference_request.status = InferenceRequest.Status.FAILED
            inference_request.error_message = f"Queue unavailable: {e}"
            inference_request.save()
            
            return Response({
                "success": False,
                "error": "Task queue unavailable",
                "request_id": str(inference_request.id)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class InferenceStatusView(APIView):
    """
    Check status of an inference request.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, request_id):
        """
        Get status and results of an inference request.
        """
        try:
            inference_request = InferenceRequest.objects.get(
                id=request_id,
                requested_by=request.user
            )
        except InferenceRequest.DoesNotExist:
            return Response(
                {"error": "Inference request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        response = {
            "request_id": str(inference_request.id),
            "status": inference_request.status,
            "created_at": inference_request.created_at.isoformat(),
        }
        
        if inference_request.started_at:
            response["started_at"] = inference_request.started_at.isoformat()
        
        if inference_request.completed_at:
            response["completed_at"] = inference_request.completed_at.isoformat()
        
        if inference_request.status == InferenceRequest.Status.SUCCESS:
            response["result"] = inference_request.result
            
        elif inference_request.status == InferenceRequest.Status.FAILED:
            response["error"] = inference_request.error_message
        
        return Response(response)


class InferenceHistoryView(APIView):
    """
    View inference request history.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List inference requests for the current user."""
        requests = InferenceRequest.objects.filter(requested_by=request.user)[:50]
        serializer = InferenceRequestSerializer(requests, many=True)
        return Response({
            "count": len(serializer.data),
            "requests": serializer.data
        })


class PredictorHealthView(APIView):
    """
    Check predictor service health.
    """
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        """Return predictor service health status."""
        health = predictor_service.health_check()
        return Response(health)
