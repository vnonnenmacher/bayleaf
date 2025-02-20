from rest_framework import permissions
from .models import Doctor

class IsDoctor(permissions.BasePermission):
    """
    Custom permission to allow access only to authenticated doctors.
    """

    def has_permission(self, request, view):
        """Check if the user is authenticated and is a doctor."""
        return bool(request.user and request.user.is_authenticated and
                    Doctor.objects.filter(id=request.user.id).exists())

    def has_object_permission(self, request, view, obj):
        """Ensure the user is a doctor."""
        return Doctor.objects.filter(id=request.user.id).exists()
