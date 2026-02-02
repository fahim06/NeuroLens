from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HealthCheckView(APIView):
    """
    Health check endpoint.
    Returns service status for monitoring and load balancers.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "service": "neurolens",
                "phase": "django-rebuild"
            },
            status=status.HTTP_200_OK
        )
