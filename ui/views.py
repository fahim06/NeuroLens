"""
UI app views for NeuroLens beta testing.
Full responsive HTML/CSS frontend using Django templates.

Phase 7: Full Responsive UI/UX Beta Interface
"""

from django.shortcuts import render, redirect
from django.views import View


class LoginView(View):
    """Login page view with animated background."""
    
    def get(self, request):
        return render(request, 'ui/login.html')


class DashboardView(View):
    """Dashboard page view with stats and quick actions."""
    
    def get(self, request):
        return render(request, 'ui/dashboard.html', {
            'active_page': 'dashboard'
        })


class DatasetsView(View):
    """Datasets management page view with upload and list."""
    
    def get(self, request):
        return render(request, 'ui/datasets.html', {
            'active_page': 'datasets'
        })


class InferenceView(View):
    """Inference page view with 2-second polling for status."""
    
    def get(self, request):
        return render(request, 'ui/inference.html', {
            'active_page': 'inference'
        })


class ProfileView(View):
    """User profile and settings page view."""
    
    def get(self, request):
        return render(request, 'ui/profile.html', {
            'active_page': 'profile'
        })


def index(request):
    """Root redirect to login or dashboard."""
    return redirect('ui:login')
