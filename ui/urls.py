"""
UI app URL configuration.
"""

from django.urls import path
from . import views

app_name = 'ui'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('datasets/', views.DatasetsView.as_view(), name='datasets'),
    path('inference/', views.InferenceView.as_view(), name='inference'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
