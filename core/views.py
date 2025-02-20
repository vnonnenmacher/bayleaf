# Create your views here.
from rest_framework import viewsets, permissions
from .models import Service
from .serializers import ServiceSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing services.
    """
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can manage services

    def get_queryset(self):
        """Return all available services."""
        return Service.objects.all()
