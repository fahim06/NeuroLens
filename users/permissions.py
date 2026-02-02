from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permission check for admin users.
    """
    message = "Admin access required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_admin


class IsBetaUser(BasePermission):
    """
    Permission check for beta users (includes admins).
    """
    message = "Beta user access required."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_beta_user


class IsAuthenticatedUser(BasePermission):
    """
    Permission check for any authenticated user.
    """
    message = "Authentication required."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
