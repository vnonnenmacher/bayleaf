from rest_framework import generics
from .serializers import PatientSerializer
from rest_framework.permissions import IsAuthenticated


class PatientCreateView(generics.CreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = []  # No authentication required for sign-up


class PatientRetrieveView(generics.RetrieveAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]  # Only authenticated users can access

    def get_object(self):
        return self.request.user
