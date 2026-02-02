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
            'created_at',
            'completed_at'
        ]
        read_only_fields = [
            'id',
            'requested_by',
            'requested_by_username',
            'status',
            'result',
            'error_message',
            'created_at',
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
    model = serializers.CharField()
    prediction = serializers.DictField()
    timestamp = serializers.CharField()
    metadata = serializers.DictField()
    request_id = serializers.UUIDField()
