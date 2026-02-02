#!/usr/bin/env python
"""Inference validation tests for Phase 4."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurolens.settings')

import django
django.setup()

import base64
from io import BytesIO
from PIL import Image
from django.test import Client
from django.contrib.auth.models import User
from users.models import UserProfile

client = Client()

print("=" * 60)
print("Phase 4 Inference Validation Tests")
print("=" * 60)

# Setup: Ensure admin user has profile and beta_user role
admin_user = User.objects.get(username='admin')
profile, _ = UserProfile.objects.get_or_create(user=admin_user)
profile.role = UserProfile.Role.BETA_USER
profile.save()

# Get token for admin user
response = client.post(
    '/api/auth/token/',
    {'username': 'admin', 'password': 'admin123'},
    content_type='application/json'
)
assert response.status_code == 200, f"Token obtain failed: {response.status_code}"
access_token = response.json()['access']
auth_header = {'HTTP_AUTHORIZATION': f'Bearer {access_token}'}

print(f"\n✓ Got auth token")

# Test 1: Predictor health endpoint
response = client.get('/api/inference/health/')
print(f"\n1. Predictor health: {response.status_code}")
health_data = response.json()
print(f"   Status: {health_data.get('status')}")
print(f"   Model loaded: {health_data.get('model_loaded')}")
print(f"   Is mock: {health_data.get('is_mock')}")
assert response.status_code == 200

# Test 2: Valid prediction with image URL
response = client.post(
    '/api/inference/predict/',
    {'image_url': 'https://example.com/test.jpg'},
    content_type='application/json',
    **auth_header
)
print(f"\n2. Predict with URL: {response.status_code}")
result = response.json()
print(f"   Success: {result.get('success')}")
print(f"   Model: {result.get('model')}")
print(f"   Is mock: {result.get('metadata', {}).get('is_mock')}")
assert response.status_code == 200
assert result.get('success') == True

# Test 3: Create a test image and encode as base64
def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (224, 224), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

test_image_b64 = create_test_image()
response = client.post(
    '/api/inference/predict/',
    {'image_data': test_image_b64},
    content_type='application/json',
    **auth_header
)
print(f"\n3. Predict with base64 image: {response.status_code}")
result = response.json()
print(f"   Success: {result.get('success')}")
print(f"   Predicted class: {result.get('prediction', {}).get('predicted_class')}")
print(f"   Confidence: {result.get('prediction', {}).get('confidence')}")
print(f"   Inference time: {result.get('metadata', {}).get('inference_time_ms')}ms")
print(f"   Is mock: {result.get('metadata', {}).get('is_mock')}")
assert response.status_code == 200

# Test 4: Invalid payload (no image)
response = client.post(
    '/api/inference/predict/',
    {'some_field': 'some_value'},
    content_type='application/json',
    **auth_header
)
print(f"\n4. Invalid payload (no image): {response.status_code}")
assert response.status_code == 400

# Test 5: Empty payload
response = client.post(
    '/api/inference/predict/',
    {},
    content_type='application/json',
    **auth_header
)
print(f"\n5. Empty payload: {response.status_code}")
assert response.status_code == 400

# Test 6: Unauthenticated request
response = client.post(
    '/api/inference/predict/',
    {'image_url': 'https://example.com/test.jpg'},
    content_type='application/json'
)
print(f"\n6. Unauthenticated request: {response.status_code}")
assert response.status_code == 401

# Test 7: Check inference history
response = client.get('/api/inference/history/', **auth_header)
print(f"\n7. Inference history: {response.status_code}")
print(f"   Total requests: {response.json().get('count')}")
assert response.status_code == 200

# Test 8: Verify no stack traces in error responses
response = client.post(
    '/api/inference/predict/',
    {'invalid': 'data'},
    content_type='application/json',
    **auth_header
)
print(f"\n8. Error response check: {response.status_code}")
response_text = response.content.decode()
assert 'Traceback' not in response_text, "Stack trace leaked in error response"
print("   ✓ No stack traces exposed")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
