from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdmin, IsBetaUser


class HealthCheckView(APIView):
    """
    Health check endpoint.
    Returns service status for monitoring and load balancers.
    Public endpoint - no authentication required.
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


class ProtectedView(APIView):
    """
    Protected endpoint - requires authentication.
    Used to verify JWT auth is working.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "message": "You are authenticated!",
                "user": request.user.username,
                "role": request.user.profile.role if hasattr(request.user, 'profile') else None
            },
            status=status.HTTP_200_OK
        )


class AdminOnlyView(APIView):
    """
    Admin-only endpoint - requires admin role.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(
            {
                "message": "Welcome, admin!",
                "user": request.user.username
            },
            status=status.HTTP_200_OK
        )


class BetaUserView(APIView):
    """
    Beta user endpoint - requires beta_user or admin role.
    """
    permission_classes = [IsBetaUser]

    def get(self, request):
        return Response(
            {
                "message": "Welcome, beta user!",
                "user": request.user.username,
                "role": request.user.profile.role
            },
            status=status.HTTP_200_OK
        )
