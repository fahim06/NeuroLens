"""
UI URL Configuration
"""

from django.urls import path

from . import views

app_name = "ui"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("datasets/", views.datasets_view, name="datasets"),
    path("inference/", views.inference_view, name="inference"),
    path("reports/", views.reports_view, name="reports"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
    path(
        "profile/notifications/",
        views.notification_settings,
        name="notification_settings",
    ),
    path("profile/privacy/", views.privacy_settings, name="privacy_settings"),
    path("profile/delete/", views.delete_account, name="delete_account"),
    path("logout/", views.logout_view, name="logout"),
]
