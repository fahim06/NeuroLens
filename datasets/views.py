from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsBetaUser
from .models import Dataset
from .serializers import DatasetSerializer, DatasetCreateSerializer


class DatasetListCreateView(APIView):
    """
    List all datasets or create a new dataset.

    GET: List datasets (authenticated users)
    POST: Create dataset (admin/beta_user only)
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsBetaUser()]
        return [IsAuthenticated()]

    def get(self, request):
        """List all datasets for the authenticated user."""
        # Users see their own datasets, admins see all
        if hasattr(request.user, "profile") and request.user.profile.is_admin:
            datasets = Dataset.objects.all()
        else:
            datasets = Dataset.objects.filter(owner=request.user)

        serializer = DatasetSerializer(datasets, many=True)
        return Response({"count": len(serializer.data), "datasets": serializer.data})

    def post(self, request):
        """Create a new dataset."""
        serializer = DatasetCreateSerializer(data=request.data)
        if serializer.is_valid():
            dataset = serializer.save(owner=request.user)
            return Response(
                DatasetSerializer(dataset).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DatasetDetailView(APIView):
    """
    Retrieve, update, or delete a specific dataset.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """Get dataset if user has access."""
        try:
            dataset = Dataset.objects.get(pk=pk)
            # Check ownership or admin access
            if dataset.owner != user:
                if not (hasattr(user, "profile") and user.profile.is_admin):
                    return None
            return dataset
        except Dataset.DoesNotExist:
            return None

    def get(self, request, pk):
        """Retrieve a dataset."""
        dataset = self.get_object(pk, request.user)
        if not dataset:
            return Response(
                {"error": "Dataset not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DatasetSerializer(dataset)
        return Response(serializer.data)

    def delete(self, request, pk):
        """Delete a dataset."""
        dataset = self.get_object(pk, request.user)
        if not dataset:
            return Response(
                {"error": "Dataset not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )
        dataset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
