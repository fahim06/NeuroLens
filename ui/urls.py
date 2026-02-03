"""
UI URL Configuration
"""
from django.urls import path
from . import views

app_name = 'ui'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('datasets/', views.datasets_view, name='datasets'),
    path('inference/', views.inference_view, name='inference'),
    path('logout/', views.logout_view, name='logout'),
]
