"""
UI Views - Django template-based frontend
"""

import pytz
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods


def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    Public endpoint - no authentication required.
    """
    return JsonResponse(
        {"status": "ok", "service": "neurolens", "phase": "django-rebuild"},
        status=200,
    )


def login_view(request):
    """
    Animated login/signup page.
    Handles both sign in and sign up via POST.
    """
    if request.user.is_authenticated:
        return redirect("ui:dashboard")

    if request.method == "POST":
        data = request.POST
        action = data.get("action", "signin")

        if action == "signup":
            # Handle registration
            name = data.get("name", "").strip()
            username = data.get("username", "").strip()
            email = data.get("email", "").strip()
            password = data.get("password", "")
            confirm_password = data.get("confirm_password", "")
            timezone = data.get("timezone", "UTC").strip()

            # Validation
            errors = {}
            if not name or len(name) < 2:
                errors["name"] = "Name must be at least 2 characters"
            if not username or len(username) < 3:
                errors["username"] = "Username must be at least 3 characters"
            if User.objects.filter(username=username).exists():
                errors["username"] = "Username already taken"
            if not email:
                errors["email"] = "Email is required"
            if User.objects.filter(email=email).exists():
                errors["email"] = "Email already registered"
            if not password or len(password) < 6:
                errors["password"] = "Password must be at least 6 characters"
            if password != confirm_password:
                errors["confirm_password"] = "Passwords do not match"

            # Validate timezone
            if timezone not in pytz.common_timezones:
                timezone = "UTC"  # Default to UTC if invalid

            if errors:
                return JsonResponse({"success": False, "errors": errors}, status=400)

            # Create user
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=name.split()[0] if name else "",
                    last_name=(
                        " ".join(name.split()[1:]) if len(name.split()) > 1 else ""
                    ),
                )
                # Set user timezone
                user.profile.timezone = timezone
                user.profile.save()
                return JsonResponse(
                    {"success": True, "message": "Account created successfully!"}
                )
            except Exception as e:
                return JsonResponse(
                    {"success": False, "errors": {"general": str(e)}}, status=400
                )

        else:
            # Handle sign in
            username = data.get("username", "").strip()
            password = data.get("password", "")

            if not username:
                return JsonResponse(
                    {"success": False, "errors": {"username": "Username is required"}},
                    status=400,
                )

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                remember_me = data.get("remember_me") == "on"
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires on browser close
                return JsonResponse({"success": True, "redirect": "/dashboard/"})
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "errors": {
                            "general": "Invalid username or password. Please try again."
                        },
                    },
                    status=401,
                )

    return render(request, "ui/login.html", {"timezones": pytz.common_timezones})


@login_required(login_url="/login/")
def dashboard_view(request):
    """Dashboard page with real-time statistics."""
    from inference.models import InferenceRequest
    from datasets.models import Dataset
    from django.db.models import Q
    from datetime import datetime, timedelta

    # Get real statistics
    total_detections = InferenceRequest.objects.filter(status="success").count()
    total_datasets = Dataset.objects.count()

    # Calculate accuracy (success rate)
    total_requests = InferenceRequest.objects.count()
    successful_requests = InferenceRequest.objects.filter(status="success").count()
    accuracy = (
        round((successful_requests / total_requests * 100), 1)
        if total_requests > 0
        else 0
    )

    # Pending analysis
    pending_count = InferenceRequest.objects.filter(
        Q(status="pending") | Q(status="processing")
    ).count()

    # Recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_activity = (
        InferenceRequest.objects.filter(created_at__gte=week_ago)
        .select_related("requested_by")
        .order_by("-created_at")[:5]
    )

    # Domain distribution (mock data for now, can be enhanced later)
    domain_stats = {
        "medical": InferenceRequest.objects.filter(status="success").count() // 3,
        "animal": InferenceRequest.objects.filter(status="success").count() // 3,
        "plant": InferenceRequest.objects.filter(status="success").count()
        - (InferenceRequest.objects.filter(status="success").count() // 3 * 2),
    }

    return render(
        request,
        "ui/dashboard.html",
        {
            "user": request.user,
            "stats": {
                "total_detections": total_detections,
                "accuracy": accuracy,
                "total_datasets": total_datasets,
                "pending_count": pending_count,
            },
            "recent_activity": recent_activity,
            "domain_stats": domain_stats,
        },
    )


@login_required(login_url="/login/")
def datasets_view(request):
    """Datasets management page."""
    return render(request, "ui/datasets.html", {"user": request.user})


@login_required(login_url="/login/")
def inference_view(request):
    """Inference page."""
    return render(request, "ui/inference.html", {"user": request.user})


@login_required(login_url="/login/")
def reports_view(request):
    """Reports and analytics page."""
    from inference.models import InferenceRequest
    from datasets.models import Dataset
    from django.db.models import Count
    from datetime import datetime, timedelta

    # Get comprehensive analytics data
    total_requests = InferenceRequest.objects.count()
    successful_requests = InferenceRequest.objects.filter(status="success").count()
    failed_requests = InferenceRequest.objects.filter(status="failed").count()

    # Success rate
    success_rate = (
        round((successful_requests / total_requests * 100), 1)
        if total_requests > 0
        else 0
    )

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    monthly_requests = InferenceRequest.objects.filter(created_at__gte=thirty_days_ago)

    # Daily breakdown for the last 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        date = datetime.now() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        day_requests = InferenceRequest.objects.filter(
            created_at__gte=date_start, created_at__lte=date_end
        ).count()

        daily_stats.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "day": date.strftime("%a"),
                "requests": day_requests,
            }
        )

    # Domain distribution
    domain_data = (
        InferenceRequest.objects.filter(status="success")
        .values("result")
        .annotate(count=Count("id"))
    )

    # Process domain data
    medical_count = 0
    animal_count = 0
    plant_count = 0

    for item in domain_data:
        result = item.get("result", {})
        if isinstance(result, dict):
            domain = result.get("domain", "").lower()
            if "medical" in domain or "brain" in domain:
                medical_count += item["count"]
            elif "animal" in domain:
                animal_count += item["count"]
            elif "plant" in domain or "citrus" in domain:
                plant_count += item["count"]

    # Model performance
    model_stats = {
        "total_datasets": Dataset.objects.count(),
        "active_models": 3,  # Medical, Animal, Plant
        "avg_processing_time": "2.3s",  # Mock data
        "uptime": "99.9%",  # Mock data
    }

    # Recent requests for table
    recent_requests = InferenceRequest.objects.select_related("requested_by").order_by(
        "-created_at"
    )[:10]

    return render(
        request,
        "ui/reports.html",
        {
            "user": request.user,
            "analytics": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": success_rate,
                "monthly_requests": monthly_requests.count(),
            },
            "daily_stats": daily_stats,
            "domain_stats": {
                "medical": medical_count,
                "animal": animal_count,
                "plant": plant_count,
            },
            "model_stats": model_stats,
            "recent_requests": recent_requests,
        },
    )


def logout_view(request):
    """Logout and redirect to login."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("ui:login")


@login_required
def profile_view(request):
    """
    User profile page.
    Shows user information and account settings.
    """
    import pytz

    user = request.user

    # Get user statistics
    from inference.models import InferenceRequest
    from datasets.models import Dataset

    total_requests = InferenceRequest.objects.filter(requested_by=user).count()
    successful_requests = InferenceRequest.objects.filter(
        requested_by=user, status="success"
    ).count()
    total_datasets = Dataset.objects.filter(owner=user).count()

    context = {
        "user": user,
        "timezones": [(tz, tz.replace("_", " ")) for tz in pytz.common_timezones],
        "stats": {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (
                (successful_requests / total_requests * 100)
                if total_requests > 0
                else 0
            ),
            "total_datasets": total_datasets,
        },
        "recent_activity": InferenceRequest.objects.filter(requested_by=user).order_by(
            "-created_at"
        )[:5],
    }

    return render(request, "ui/profile.html", context)


@login_required
def edit_profile(request):
    """
    Handle profile editing with file upload support.
    """
    import pytz

    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        timezone = request.POST.get("timezone", "UTC").strip()
        profile_picture = request.FILES.get("profile_picture")
        remove_picture = request.POST.get("remove_picture") == "1"

        # Validation
        errors = []
        if not email:
            errors.append("Email is required.")
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            errors.append("This email is already in use.")

        # Validate timezone
        if timezone not in pytz.common_timezones:
            errors.append("Invalid timezone selected.")

        # Validate profile picture
        if profile_picture:
            # Check file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                errors.append("Profile picture must be smaller than 5MB.")

            # Check file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if profile_picture.content_type not in allowed_types:
                errors.append(
                    "Profile picture must be a JPEG, PNG, GIF, or WebP image."
                )

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update user basic info
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            # Update timezone
            user.profile.timezone = timezone
            user.profile.save()

            # Handle profile picture
            if remove_picture and user.profile.profile_picture:
                # Delete the old picture file
                user.profile.profile_picture.delete(save=False)
                user.profile.profile_picture = None
                user.profile.save()
            elif profile_picture:
                # If there's an existing picture, delete it first
                if user.profile.profile_picture:
                    user.profile.profile_picture.delete(save=False)
                user.profile.profile_picture = profile_picture
                user.profile.save()

            messages.success(request, "Profile updated successfully!")

    return redirect("ui:profile")


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """
    Handle password change and current password validation.
    """
    user = request.user

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # AJAX validation for current password only
        if current_password and not new_password and not confirm_password:
            if user.check_password(current_password):
                return JsonResponse({"valid": True})
            else:
                return JsonResponse(
                    {"valid": False, "error": "Current password is incorrect."}
                )

        # Full password change validation
        errors = []
        if not user.check_password(current_password):
            errors.append("Current password is incorrect.")
        if not new_password or len(new_password) < 6:
            errors.append("New password must be at least 6 characters long.")
        if new_password != confirm_password:
            errors.append("New passwords do not match.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Password changed successfully!")

    return redirect("ui:profile")


@login_required
@require_http_methods(["POST"])
def notification_settings(request):
    """
    Handle notification settings update.
    """
    user = request.user

    if request.method == "POST":
        # For now, we'll just show a success message
        # In a real app, you'd save these to a UserProfile model
        email_notifications = request.POST.get("email_notifications") == "on"
        analysis_complete = request.POST.get("analysis_complete") == "on"
        weekly_reports = request.POST.get("weekly_reports") == "on"

        # TODO: Save to user profile model when implemented
        messages.success(request, "Notification settings updated successfully!")

    return redirect("ui:profile")


@login_required
@require_http_methods(["POST"])
def privacy_settings(request):
    """
    Handle privacy settings update.
    """
    user = request.user

    if request.method == "POST":
        # For now, we'll just show a success message
        # In a real app, you'd save these to a UserProfile model
        profile_visible = request.POST.get("profile_visible") == "on"
        data_sharing = request.POST.get("data_sharing") == "on"
        analytics_tracking = request.POST.get("analytics_tracking") == "on"

        # TODO: Save to user profile model when implemented
        messages.success(request, "Privacy settings updated successfully!")

    return redirect("ui:profile")


@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """
    Handle account deletion.
    """
    user = request.user

    if request.method == "POST":
        confirm_username = request.POST.get("confirm_username", "").strip()

        if confirm_username != user.username:
            messages.error(request, "Username confirmation does not match.")
        else:
            # Delete all user's data
            from inference.models import InferenceRequest
            from datasets.models import Dataset

            # Delete user's inference requests
            InferenceRequest.objects.filter(requested_by=user).delete()

            # Delete user's datasets
            Dataset.objects.filter(owner=user).delete()

            # Delete the user account
            user.delete()

            messages.success(request, "Your account has been successfully deleted.")
            return redirect("ui:login")

    return redirect("ui:profile")
