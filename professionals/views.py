from rest_framework import generics, viewsets, permissions
from rest_framework import status
from .serializers import ProfessionalSerializer, RoleSerializer, ShiftSerializer
from rest_framework.response import Response
from .models import Professional, Role, Shift


class ProfessionalCreateView(generics.CreateAPIView):
    serializer_class = ProfessionalSerializer
    permission_classes = []  # No authentication required for registration


class ProfessionalRetrieveView(generics.RetrieveAPIView):
    serializer_class = ProfessionalSerializer
    permission_classes = [permissions.IsAuthenticated]  # Use the app-specific permission

    def get_object(self):
        """Ensure the authenticated user is retrieved as a Professional instance."""
        user = self.request.user
        return Professional.objects.select_related().filter(id=user.id).first()


class ShiftViewSet(viewsets.ModelViewSet):
    """
    API endpoint for doctors to manage their shifts.
    """
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the shifts of the logged-in doctor."""
        professional = Professional.objects.filter(user_ptr_id=self.request.user.id).first()  # ✅ Fix
        if professional:
            return Shift.objects.filter(professional=professional)
        return Shift.objects.none()  # If the user is not a doctor, return empty queryset

    def perform_create(self, serializer):
        """Assign the shift to the logged-in doctor."""
        professional = Professional.objects.filter(user_ptr_id=self.request.user.id).first()  # ✅ Fix
        if not professional:
            return Response({"error": "User is not a doctor"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(professional=professional)


class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing professional roles.
    """
    serializer_class = RoleSerializer
    queryset = Role.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class ProfessionalUpdateView(generics.RetrieveUpdateAPIView):
    """API endpoint for doctors to update their profile (including identifiers)."""

    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        try:
            return Professional.objects.get(user_ptr_id=user.id)  # ✅ Correct lookup
        except Professional.DoesNotExist:
            raise Professional.DoesNotExist("The logged-in user is not a registered doctor.")
