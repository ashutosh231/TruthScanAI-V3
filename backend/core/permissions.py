"""
Permission classes for TruthScan DRF endpoints.
"""

from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

class IsAuthenticatedMongoUser(permissions.BasePermission):
    """
    Requires the request to have a valid authenticated MongoUser.
    Returns 401 (AuthenticationFailed) if unauthenticated.
    """
    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            raise AuthenticationFailed("Access denied. No authentication token provided.")
        return True


class IsAdminMongoUser(permissions.BasePermission):
    """
    Requires the request to have an authenticated user with role == 'admin'.
    """
    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            raise AuthenticationFailed("Access denied. No authentication token provided.")
        if getattr(request.user, "role", None) != "admin":
            raise PermissionDenied(f"Access forbidden: User role '{request.user.role}' is not authorized.")
        return True
