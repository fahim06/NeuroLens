"""
UI app views for NeuroLens beta testing.
Simple HTML/CSS frontend using Django templates.
"""

from django.shortcuts import render, redirect
from django.views import View


class LoginView(View):
    """Login page view."""
    
    def get(self, request):
        return render(request, 'ui/login.html')


class DashboardView(View):
    """Dashboard page view."""
    
    def get(self, request):
        return render(request, 'ui/dashboard.html')


class DatasetsView(View):
    """Datasets management page view."""
    
    def get(self, request):
        return render(request, 'ui/datasets.html')


class InferenceView(View):
    """Inference page view."""
    
    def get(self, request):
        return render(request, 'ui/inference.html')


def index(request):
    """Root redirect to login or dashboard."""
    return redirect('ui:login')
