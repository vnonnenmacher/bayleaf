# Create your views here.
from rest_framework import viewsets, permissions
from .models import Service
from .serializers import ServiceSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
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
