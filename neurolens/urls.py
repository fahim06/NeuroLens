"""
URL configuration for neurolens project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

# Universal error handlers - work regardless of DEBUG=True/False
from ui.error_views import error_404, error_403, error_500

handler404 = error_404
handler403 = error_403
handler500 = error_500


def api_root(request):
    """API root endpoint."""
    return JsonResponse(
        {
            "name": "NeuroLens API",
            "version": "2.1.2--beta",
            "docs": "/api/docs/",
            "health": "/api/health/",
        }
    )


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # UI Routes (Django templates + Tailwind) - Phase 9
    path("", include("ui.urls")),
    # API Routes
    path("api/auth/", include("users.urls")),
    path("api/datasets/", include("datasets.urls")),
    path("api/inference/", include("inference.urls")),
    path("api/ml/", include("ml.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
