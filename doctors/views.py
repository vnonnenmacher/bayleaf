from rest_framework import generics, viewsets, permissions
from rest_framework import status
from doctors.permissions import IsDoctor
from .serializers import DoctorSerializer, ShiftSerializer
from rest_framework.response import Response
from .models import Doctor, Shift


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


class ShiftViewSet(viewsets.ModelViewSet):
    """
    API endpoint for doctors to manage their shifts.
    """
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def get_queryset(self):
        """Return only the shifts of the logged-in doctor."""
        return Shift.objects.filter(doctor=self.request.user)

    def perform_create(self, serializer):
        """Assign the shift to the logged-in doctor."""
        doctor = Doctor.objects.filter(id=self.request.user.id).first()
        if not doctor:
            return Response({"error": "User is not a doctor"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(doctor=doctor)


class DoctorUpdateView(generics.RetrieveUpdateAPIView):
    """API endpoint for doctors to update their Address & Contact details."""
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Ensure the authenticated user is returned as a `Doctor` object."""
        return Doctor.objects.get(pk=self.request.user.pk)
