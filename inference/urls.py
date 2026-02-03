from django.urls import path
from .views import (
    PredictView,
    AsyncPredictView,
    InferenceStatusView,
    InferenceHistoryView,
    PredictorHealthView,
    DetectView,
    DetectionTypesView,
    AutoAnalyzeView
)

app_name = 'inference'

urlpatterns = [
    # Phase 10: Multi-domain detection endpoints
    path('analyze/', AutoAnalyzeView.as_view(), name='analyze'),  # Auto-detect & classify
    path('detect/', DetectView.as_view(), name='detect'),
    path('detection-types/', DetectionTypesView.as_view(), name='detection-types'),
    
    # Legacy prediction endpoints (still functional)
    path('predict/', PredictView.as_view(), name='predict'),
    path('predict/async/', AsyncPredictView.as_view(), name='predict-async'),
    path('<uuid:request_id>/status/', InferenceStatusView.as_view(), name='status'),
    path('history/', InferenceHistoryView.as_view(), name='history'),
    path('health/', PredictorHealthView.as_view(), name='predictor-health'),
]
