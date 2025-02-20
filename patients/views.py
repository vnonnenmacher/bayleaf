from rest_framework import generics

from patients.permissions import IsPatient
from .serializers import PatientSerializer
from .models import Patient


class PatientCreateView(generics.CreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = []  # No authentication required for sign-up


class PatientRetrieveView(generics.RetrieveAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsPatient]  # Use the app-specific permission

    def get_object(self):
        """Ensure the authenticated user is retrieved as a Patient instance."""
        user = self.request.user
        return Patient.objects.select_related().filter(id=user.id).first()
