"""
Celery Configuration for NeuroLens.

This module initializes the Celery application for async task processing.
Used primarily for background inference jobs.
"""
import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurolens.settings')

# Create Celery app
app = Celery('neurolens')

# Load configuration from Django settings
# All Celery settings should be prefixed with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connectivity."""
    print(f'Request: {self.request!r}')
