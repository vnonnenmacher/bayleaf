from rest_framework import permissions

from users.permissions import IsBayleafAPIToken
from .models import Professional


class IsProfessional(permissions.BasePermission):
    """
    Custom permission to allow access only to authenticated professionals.
    """

    def has_permission(self, request, view):
        """Check if the user is authenticated and is a professional."""
        return bool(request.user and request.user.is_authenticated and
                    Professional.objects.filter(id=request.user.id).exists())

    def has_object_permission(self, request, view, obj):
        """Ensure the user is a professional."""
        return Professional.objects.filter(id=request.user.id).exists()


class IsAgentOrProfessional(permissions.BasePermission):
    def has_permission(self, request, view):
        return IsBayleafAPIToken().has_permission(request, view) or IsProfessional().has_permission(request, view)