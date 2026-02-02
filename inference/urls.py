from django.urls import path
from .views import PredictView, InferenceHistoryView, PredictorHealthView

app_name = 'inference'

urlpatterns = [
    path('predict/', PredictView.as_view(), name='predict'),
    path('history/', InferenceHistoryView.as_view(), name='history'),
    path('health/', PredictorHealthView.as_view(), name='predictor-health'),
]
