from rest_framework import permissions
from .models import Patient


class IsPatient(permissions.BasePermission):
    """
    Custom permission to allow access only to authenticated patients.
    """

    def has_permission(self, request, view):
        """Check if the user is authenticated and is a patient."""
        return bool(request.user and request.user.is_authenticated and
                    Patient.objects.filter(id=request.user.id).exists())

    def has_object_permission(self, request, view, obj):
        """Ensure the user is a patient."""
        return Patient.objects.filter(id=request.user.id).exists()
