#!/usr/bin/env python
"""
Phase 5 Beta Stability Tests.

Tests for async inference, logging, and graceful degradation.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurolens.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import json
import base64
import uuid
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from inference.models import InferenceRequest


def create_test_image():
    """Create a small test image."""
    img = Image.new('RGB', (32, 32), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


class Phase5StabilityTests(TestCase):
    """Test suite for Phase 5 beta stability."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        # Get auth token
        response = self.client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.test_image = create_test_image()
    
    def test_sync_predict_endpoint(self):
        """Test synchronous prediction endpoint."""
        response = self.client.post('/api/inference/predict/', {
            'image_data': self.test_image
        }, format='json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('request_id', data)
        self.assertIn('prediction', data)
    
    def test_async_predict_endpoint(self):
        """Test async prediction endpoint returns 202 or 503."""
        response = self.client.post('/api/inference/predict/async/', {
            'image_data': self.test_image
        }, format='json')
        
        # Either accepted (Redis running) or service unavailable (Redis down)
        self.assertIn(response.status_code, [202, 503])
        
        if response.status_code == 202:
            data = response.json()
            self.assertTrue(data.get('success'))
            self.assertIn('request_id', data)
            self.assertIn('status_url', data)
    
    def test_status_endpoint(self):
        """Test inference status endpoint."""
        # Create a request first
        inference_request = InferenceRequest.objects.create(
            requested_by=self.user,
            status='success',
            result={'prediction': {'predicted_class': 'test'}}
        )
        
        response = self.client.get(f'/api/inference/{inference_request.id}/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('result', data)
    
    def test_status_endpoint_not_found(self):
        """Test status endpoint with invalid ID."""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/inference/{fake_id}/status/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_status_endpoint_other_user(self):
        """Test status endpoint blocks access to other users' requests."""
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        inference_request = InferenceRequest.objects.create(
            requested_by=other_user,
            status='success'
        )
        
        response = self.client.get(f'/api/inference/{inference_request.id}/status/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_inference_request_fields(self):
        """Test InferenceRequest model has async fields."""
        request = InferenceRequest.objects.create(
            requested_by=self.user,
            status='pending',
            celery_task_id='test-task-123'
        )
        
        self.assertEqual(request.celery_task_id, 'test-task-123')
        self.assertIsNone(request.started_at)
    
    def test_prediction_creates_inference_record(self):
        """Test that predictions create InferenceRequest records."""
        initial_count = InferenceRequest.objects.count()
        
        self.client.post('/api/inference/predict/', {
            'image_data': self.test_image
        }, format='json')
        
        self.assertEqual(InferenceRequest.objects.count(), initial_count + 1)
    
    def test_history_endpoint(self):
        """Test inference history endpoint."""
        # Create some requests
        for i in range(3):
            InferenceRequest.objects.create(
                requested_by=self.user,
                status='success'
            )
        
        response = self.client.get('/api/inference/history/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 3)
    
    def test_predictor_health(self):
        """Test predictor health endpoint."""
        response = self.client.get('/api/inference/health/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
    
    def test_invalid_payload_rejected(self):
        """Test that invalid payloads are rejected."""
        response = self.client.post('/api/inference/predict/', {}, format='json')
        
        self.assertEqual(response.status_code, 400)
    
    def test_unauthenticated_rejected(self):
        """Test that unauthenticated requests are rejected."""
        client = APIClient()  # No auth
        response = client.post('/api/inference/predict/', {
            'image_data': self.test_image
        }, format='json')
        
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    import unittest
    
    print("=" * 60)
    print("Phase 5 Beta Stability Tests")
    print("=" * 60)
    
    # Run as Django tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Phase5StabilityTests)
    result = test_runner.run_suite(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("ALL TESTS PASSED!")
    else:
        print(f"FAILURES: {len(result.failures)}")
        print(f"ERRORS: {len(result.errors)}")
    print("=" * 60)
    
    sys.exit(0 if result.wasSuccessful() else 1)
