from django.urls import path
from .views import (
    PredictView,
    AsyncPredictView,
    InferenceStatusView,
    InferenceHistoryView,
    PredictorHealthView
)

app_name = 'inference'

urlpatterns = [
    path('predict/', PredictView.as_view(), name='predict'),
    path('predict/async/', AsyncPredictView.as_view(), name='predict-async'),
    path('<uuid:request_id>/status/', InferenceStatusView.as_view(), name='status'),
    path('history/', InferenceHistoryView.as_view(), name='history'),
    path('health/', PredictorHealthView.as_view(), name='predictor-health'),
]
