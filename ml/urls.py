"""
ML URLs — API Endpoints

URL patterns for ML API endpoints.
"""

from django.urls import path
from . import views

app_name = "ml"

urlpatterns = [
    # Health check
    path("health/", views.health_check, name="health_check"),
    # Model information
    path("models/", views.available_models, name="available_models"),
    # Inference endpoints
    path("detect-domain/", views.detect_domain, name="detect_domain"),
    path("predict/", views.predict, name="predict"),
]
