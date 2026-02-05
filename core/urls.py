from django.urls import path

from .views import HealthCheckView, ProtectedView, AdminOnlyView, BetaUserView

app_name = "core"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("protected/", ProtectedView.as_view(), name="protected"),
    path("admin-only/", AdminOnlyView.as_view(), name="admin-only"),
    path("beta/", BetaUserView.as_view(), name="beta"),
]
