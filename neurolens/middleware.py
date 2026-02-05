"""
Timezone Middleware for User-Specific Timezone Support

This middleware activates the user's timezone for each request,
ensuring that dates and times are displayed in the user's local timezone.
"""
import pytz
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
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
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
