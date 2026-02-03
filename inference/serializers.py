from rest_framework import serializers
from .models import InferenceRequest


class InferenceRequestSerializer(serializers.ModelSerializer):
    """Serializer for InferenceRequest model."""
    
    requested_by_username = serializers.ReadOnlyField(source='requested_by.username')
    dataset_name = serializers.ReadOnlyField(source='dataset.name')
    
    class Meta:
        model = InferenceRequest
        fields = [
            'id',
            'requested_by',
            'requested_by_username',
            'dataset',
            'dataset_name',
            'status',
            'input_data',
            'result',
            'error_message',
            'celery_task_id',
            'created_at',
            'started_at',
            'completed_at'
        ]
        read_only_fields = [
            'id',
            'requested_by',
            'requested_by_username',
            'status',
            'result',
            'error_message',
            'celery_task_id',
            'created_at',
            'started_at',
            'completed_at'
        ]


class PredictRequestSerializer(serializers.Serializer):
    """Serializer for prediction request input."""
    
    image_data = serializers.CharField(
        required=False,
        help_text="Base64 encoded image data"
    )
    image_url = serializers.URLField(
        required=False,
        help_text="URL to the image"
    )
    dataset_id = serializers.UUIDField(
        required=False,
        help_text="Optional dataset ID for context"
    )
    detection_type = serializers.ChoiceField(
        required=False,
        choices=[
            ('human_animal', 'Human vs Animal Detection'),
            ('animal_category', 'Animal Category Detection'),
            ('biological', 'Biological Classification'),
            ('brain_tumor', 'Brain Tumor Detection'),
            ('citrus', 'Citrus Classification'),
        ],
        help_text="Type of detection to perform"
    )
    
    def validate(self, attrs):
        """Ensure at least one image source is provided."""
        if not attrs.get('image_data') and not attrs.get('image_url'):
            raise serializers.ValidationError(
                "Either 'image_data' or 'image_url' must be provided."
            )
        return attrs


class PredictResponseSerializer(serializers.Serializer):
    """Serializer for prediction response output."""
    
    success = serializers.BooleanField()
    detection_type = serializers.CharField(required=False)
    detection_name = serializers.CharField(required=False)
    prediction = serializers.DictField()
    timestamp = serializers.CharField()
    metadata = serializers.DictField(required=False)
    request_id = serializers.UUIDField(required=False)


class DetectRequestSerializer(serializers.Serializer):
    """
    Serializer for multi-domain detection request.
    Phase 10: POST /api/inference/detect/
    """
    
    detection_type = serializers.ChoiceField(
        required=True,
        choices=[
            ('human_animal', 'Human vs Animal Detection'),
            ('animal_category', 'Animal Category Detection'),
            ('biological', 'Biological Classification'),
            ('brain_tumor', 'Brain Tumor Detection'),
            ('citrus', 'Citrus Classification'),
        ],
        help_text="Type of detection to perform (required)"
    )
    image_data = serializers.CharField(
        required=False,
        help_text="Base64 encoded image data"
    )
    image_url = serializers.URLField(
        required=False,
        help_text="URL to the image"
    )
    
    def validate(self, attrs):
        """Ensure detection_type and at least one image source is provided."""
        if not attrs.get('image_data') and not attrs.get('image_url'):
            raise serializers.ValidationError(
                "Either 'image_data' or 'image_url' must be provided."
            )
        return attrs


class AutoAnalyzeRequestSerializer(serializers.Serializer):
    """
    Serializer for auto-analyze request.
    Phase 10: POST /api/inference/analyze/
    
    The user never selects the model — the system does.
    """
    
    image_data = serializers.CharField(
        required=False,
        help_text="Base64 encoded image data"
    )
    image_url = serializers.URLField(
        required=False,
        help_text="URL to the image"
    )
    
    def validate(self, attrs):
        """Ensure at least one image source is provided."""
        if not attrs.get('image_data') and not attrs.get('image_url'):
            raise serializers.ValidationError(
                "Either 'image_data' or 'image_url' must be provided."
            )
        return attrs

