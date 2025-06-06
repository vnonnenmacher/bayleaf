from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, permissions, filters
from rest_framework import status

from appointments.models import Appointment
from appointments.serializers import AppointmentListSerializer
from .serializers import ProfessionalSerializer, RoleSerializer, ShiftSerializer, SpecializationSerializer
from rest_framework.response import Response
from .models import Professional, Role, Shift, Specialization
from django.utils.timezone import now


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


class ProfessionalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfessionalSerializer
    queryset = Professional.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role']  # ✅ role can be handled automatically
    search_fields = ['first_name', 'last_name', 'email']

    ordering = ['last_name', 'first_name']

    def get_queryset(self):
        queryset = super().get_queryset().order_by('last_name', 'first_name')  # ✅ Safe ordering

        service_ids = self.request.query_params.getlist("service_ids")
        if service_ids:
            queryset = queryset.filter(services__id__in=service_ids)

        specialization_ids = self.request.query_params.getlist("specialization_ids")
        if specialization_ids:
            queryset = queryset.filter(specializations__id__in=specialization_ids)

        return queryset.distinct()


class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfessionalAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from appointments.filters import apply_appointment_filters  # or define it above

        try:
            professional = Professional.objects.get(user_ptr_id=self.request.user.id)
        except Professional.DoesNotExist:
            return Appointment.objects.none()

        qs = Appointment.objects.filter(professional=professional)
        return apply_appointment_filters(qs, self.request).order_by("-scheduled_to")


class NextProfessionalAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            professional = Professional.objects.get(user_ptr_id=self.request.user.id)
        except Professional.DoesNotExist:
            return Appointment.objects.none()

        return (
            Appointment.objects
            .filter(
                professional=professional,
                scheduled_to__gte=now(),
            )
            .exclude(status__in=["CANCELED", "COMPLETED"])
            .order_by("scheduled_to")
        )
