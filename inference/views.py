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
    PredictResponseSerializer
)
from .services.predictor import predictor_service


class PredictView(APIView):
    """
    Handle prediction requests.
    
    POST: Submit an image for prediction
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Process a prediction request.
        
        Accepts image data and returns prediction results.
        """
        # Validate input
        serializer = PredictRequestSerializer(data=request.data)
        if not serializer.is_valid():
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
            input_data={
                "has_image_data": bool(validated_data.get('image_data')),
                "image_url": validated_data.get('image_url')
            }
        )
        
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
            
            return Response(prediction_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Handle prediction failure
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
