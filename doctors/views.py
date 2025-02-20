from rest_framework import generics
from doctors.permissions import IsDoctor
from .serializers import DoctorSerializer
from .models import Doctor


class DoctorCreateView(generics.CreateAPIView):
    serializer_class = DoctorSerializer
    permission_classes = []  # No authentication required for registration


class DoctorRetrieveView(generics.RetrieveAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [IsDoctor]  # Use the app-specific permission

    def get_object(self):
        """Ensure the authenticated user is retrieved as a Doctor instance."""
        user = self.request.user
        return Doctor.objects.select_related().filter(id=user.id).first()
