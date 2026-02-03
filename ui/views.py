"""
UI Views - Django template-based frontend
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json


def login_view(request):
    """
    Animated login/signup page.
    Handles both sign in and sign up via POST.
    """
    if request.user.is_authenticated:
        return redirect('ui:dashboard')

    if request.method == 'POST':
        data = request.POST
        action = data.get('action', 'signin')

        if action == 'signup':
            # Handle registration
            name = data.get('name', '').strip()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')

            # Validation
            errors = {}
            if not name or len(name) < 2:
                errors['name'] = 'Name must be at least 2 characters'
            if not username or len(username) < 3:
                errors['username'] = 'Username must be at least 3 characters'
            if User.objects.filter(username=username).exists():
                errors['username'] = 'Username already taken'
            if not email:
                errors['email'] = 'Email is required'
            if User.objects.filter(email=email).exists():
                errors['email'] = 'Email already registered'
            if not password or len(password) < 6:
                errors['password'] = 'Password must be at least 6 characters'
            if password != confirm_password:
                errors['confirm_password'] = 'Passwords do not match'

            if errors:
                return JsonResponse({'success': False, 'errors': errors}, status=400)

            # Create user
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=name.split()[0] if name else '',
                    last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
                )
                return JsonResponse({
                    'success': True,
                    'message': 'Account created successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': {'general': str(e)}
                }, status=400)

        else:
            # Handle sign in
            email = data.get('email', '').strip()
            password = data.get('password', '')

            # Try to find user by email
            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
            except User.DoesNotExist:
                username = email  # Fall back to treating email as username

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                remember_me = data.get('remember_me') == 'on'
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires on browser close
                return JsonResponse({
                    'success': True,
                    'redirect': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': {'general': 'Invalid credentials. Please try again.'}
                }, status=401)

    return render(request, 'ui/login.html')


@login_required(login_url='/login/')
def dashboard_view(request):
    """Dashboard page."""
    return render(request, 'ui/dashboard.html', {
        'user': request.user
    })


@login_required(login_url='/login/')
def datasets_view(request):
    """Datasets management page."""
    return render(request, 'ui/datasets.html', {
        'user': request.user
    })


@login_required(login_url='/login/')
def inference_view(request):
    """Inference page."""
    return render(request, 'ui/inference.html', {
        'user': request.user
    })


def logout_view(request):
    """Logout and redirect to login."""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('ui:login')
