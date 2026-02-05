from django.urls import path

from .views import DatasetListCreateView, DatasetDetailView

app_name = "datasets"

urlpatterns = [
    path("", DatasetListCreateView.as_view(), name="dataset-list-create"),
    path("<uuid:pk>/", DatasetDetailView.as_view(), name="dataset-detail"),
]
