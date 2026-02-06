"""
Timezone Middleware for User-Specific Timezone Support

This middleware activates the user's timezone for each request,
ensuring that dates and times are displayed in the user's local timezone.
"""

import pytz
from django.shortcuts import render
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to activate user's timezone for each request.

    This ensures that all datetime operations in templates and views
    respect the user's timezone preference.
    """

    def process_request(self, request):
        """
        Activate the user's timezone for the current request.

        If the user is authenticated and has a timezone set,
        activate that timezone. Otherwise, use UTC.
        """
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            user_timezone = request.user.profile.timezone
            if user_timezone in pytz.common_timezones:
                try:
                    timezone.activate(pytz.timezone(user_timezone))
                except pytz.exceptions.UnknownTimeZoneError:
                    # Fallback to UTC if timezone is invalid
                    timezone.activate(pytz.UTC)
            else:
                # Fallback to UTC if timezone is not in common timezones
                timezone.activate(pytz.UTC)
        else:
            # For anonymous users, use UTC
            timezone.activate(pytz.UTC)


class CustomErrorMiddleware(MiddlewareMixin):
    """
    Middleware to show custom error pages even when DEBUG=True.

    This middleware intercepts 404, 403, and 500 responses and replaces
    them with custom templates, ensuring consistent error pages in development.
    """

    def process_response(self, request, response):
        """
        Process the response and replace debug error pages with custom ones.
        """
        if response.status_code in [404, 403, 500]:
            # Check if this is Django's debug error page (contains debug toolbar or debug info)
            response_content = response.content.decode("utf-8", errors="ignore")

            # Django debug pages typically contain these indicators
            debug_indicators = [
                "DEBUG = True",
                "Page not found at",
                "Server Error (500)",
                "Forbidden (403)",
                "You're seeing this error because you have DEBUG = True",
            ]

            is_debug_page = any(
                indicator in response_content for indicator in debug_indicators
            )

            if is_debug_page:
                # Replace with custom error page
                if response.status_code == 404:
                    response = render(request, "404.html", status=404)
                elif response.status_code == 403:
                    response = render(request, "403.html", status=403)
                elif response.status_code == 500:
                    response = render(request, "500.html", status=500)

        return response


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to activate user's timezone for each request.

    This ensures that all datetime operations in templates and views
    respect the user's timezone preference.
    """

    def process_request(self, request):
        """
        Activate the user's timezone for the current request.

        If the user is authenticated and has a timezone set,
        activate that timezone. Otherwise, use UTC.
        """
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            user_timezone = request.user.profile.timezone
            if user_timezone in pytz.common_timezones:
                try:
                    timezone.activate(pytz.timezone(user_timezone))
                except pytz.exceptions.UnknownTimeZoneError:
                    # Fallback to UTC if timezone is invalid
                    timezone.activate(pytz.UTC)
            else:
                # Fallback to UTC if timezone is not in common timezones
                timezone.activate(pytz.UTC)
        else:
            # For anonymous users, use UTC
            timezone.activate(pytz.UTC)
