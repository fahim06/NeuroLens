from rest_framework import serializers

from .models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for Dataset model."""

    owner_username = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "description",
            "domain",
            "classes",
            "version",
            "source",
            "active",
            "owner",
            "owner_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "owner_username", "created_at", "updated_at"]


class DatasetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Dataset."""

    class Meta:
        model = Dataset
        fields = [
            "name",
            "description",
            "domain",
            "classes",
            "version",
            "source",
            "active",
        ]

    def validate_name(self, value):
        """Ensure dataset name is not empty and has reasonable length."""
        if not value or not value.strip():
            raise serializers.ValidationError("Dataset name cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError(
                "Dataset name cannot exceed 255 characters."
            )
        return value.strip()
