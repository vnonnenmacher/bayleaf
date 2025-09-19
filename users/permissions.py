from django.conf import settings
from rest_framework.permissions import BasePermission


class IsBayleafAPIToken(BasePermission):
    """
    Require aud=bayleaf-api. Optionally require scopes by setting
    `required_scopes = ["user.read"]` on the view.
    """
    def has_permission(self, request, view):
        token = getattr(request, "auth", None) or {}
        if token.get("aud") != getattr(settings, "BAYLEAF_AUDIENCE_API", "bayleaf-api"):
            return False
        required = getattr(view, "required_scopes", [])
        if required:
            scopes = (token.get("scope") or "").split()
            return any(s in scopes for s in required)
        return True
