# Create your views here.
from rest_framework import viewsets, permissions
from .models import Service
from .serializers import ServiceSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def healthcheck(request):
    return Response({"status": "ok"}, status=200)


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing services.
    """
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can manage services

    def get_queryset(self):
        """Return all available services."""
        return Service.objects.all()
