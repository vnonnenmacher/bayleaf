from rest_framework import permissions
from .models import Patient


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and Patient.objects.filter(user_ptr_id=request.user.id).exists()
        )

    def has_object_permission(self, request, view, obj):
        return Patient.objects.filter(user_ptr_id=request.user.id).exists()
