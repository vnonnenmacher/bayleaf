# patients/views.py
from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django.utils.timezone import now

from appointments.models import Appointment
from appointments.serializers import AppointmentListSerializer
from appointments.filters import apply_appointment_filters

from professionals.models import Professional
from professionals.serializers import ProfessionalListSerializer

from users.permissions import IsBayleafAPIToken

from patients.permissions import IsPatient
from patients.models import Patient, Relative, PatientRelationship
from patients.serializers import (
    PatientSerializer,
    # relative serializers (final)
    RelativeSerializer,
    AddManagedPatientSerializer,
    LinkExistingPatientSerializer,
    PatientRelationshipToggleActiveSerializer,
)


# =========================================
# Existing Patient endpoints (kept as-is)
# =========================================

class PatientCreateView(generics.CreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = []  # No authentication required for sign-up


class PatientRetrieveView(generics.RetrieveAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsPatient | IsBayleafAPIToken]

    def get_object(self):
        user = self.request.user
        return Patient.objects.select_related().get(user_ptr_id=user.id)


class PatientUpdateView(generics.RetrieveUpdateAPIView):
    """API endpoint for patients to update their Address & Contact details."""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve the logged-in user's Patient profile correctly."""
        user = self.request.user
        try:
            return Patient.objects.get(user_ptr_id=user.id)
        except Patient.DoesNotExist:
            raise Patient.DoesNotExist("The logged-in user is not a registered patient.")


class PatientListView(generics.ListAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]  # Customize this as needed

    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name", "email"]


class PatientAppointmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user_ptr_id=request.user.id)
        except Patient.DoesNotExist:
            return Response({"appointments": [], "professionals": []})

        qs = Appointment.objects.filter(patient=patient)
        appointments = apply_appointment_filters(qs, request).order_by("-created_at")

        # ✅ Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10  # or add page_size_query_param on the paginator class

        paginated_appointments = paginator.paginate_queryset(appointments, request)
        appointment_serializer = AppointmentListSerializer(paginated_appointments, many=True)

        # ✅ Extract professional UUIDs from paginated list only
        professional_ids = {appt.professional_id for appt in paginated_appointments}
        professionals = Professional.objects.filter(did__in=professional_ids)
        professional_serializer = ProfessionalListSerializer(professionals, many=True)

        # ✅ Return paginated response manually
        return paginator.get_paginated_response({
            "appointments": appointment_serializer.data,
            "professionals": professional_serializer.data,
        })


class NextAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            patient = Patient.objects.get(user_ptr_id=self.request.user.id)
        except Patient.DoesNotExist:
            return Appointment.objects.none()

        return (
            Appointment.objects
            .filter(
                patient=patient,
                scheduled_to__gte=now(),
            )
            .exclude(status__in=["CANCELED", "COMPLETED"])
            .order_by("scheduled_to")
        )


# =========================================
# New: Relative & Relationship endpoints
# =========================================

class RelativeCreateView(generics.CreateAPIView):
    """
    Create a Relative user (signup).
    Uses unified RelativeSerializer (supports nested address/contact on create).
    """
    serializer_class = RelativeSerializer
    permission_classes = []  # allow public signup for relatives


class RelativeMeView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/patients/relatives/me/   -> profile w/ patient links
    PATCH/PUT                            -> update profile + nested address/contact
    """
    serializer_class = RelativeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # With multi-table inheritance, if this user is a Relative, request.user.relative exists.
        rel = getattr(self.request.user, "relative", None)
        if not isinstance(rel, Relative):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Logged-in user is not a Relative.")
        return rel


class RelativeAddManagedPatientView(generics.CreateAPIView):
    """
    Relative creates a new managed Patient (no login yet),
    backend generates placeholder email, and links it (PatientRelationship.active=...).
    """
    serializer_class = AddManagedPatientSerializer
    permission_classes = [permissions.IsAuthenticated]


class RelativeLinkExistingPatientView(generics.CreateAPIView):
    """
    Relative links an existing Patient to themselves (no deletion supported here).
    """
    serializer_class = LinkExistingPatientSerializer
    permission_classes = [permissions.IsAuthenticated]


class PatientRelationshipToggleActiveView(generics.UpdateAPIView):
    """
    Toggle relationship `active` (inactivate/reactivate). No delete.
    Only the owner Relative can change it.
    """
    serializer_class = PatientRelationshipToggleActiveSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        """
        Scope queryset so a relative can only toggle their own relationships.
        """
        rel = getattr(self.request.user, "relative", None)
        if not isinstance(rel, Relative):
            # Empty queryset for non-relatives
            return PatientRelationship.objects.none()
        return PatientRelationship.objects.filter(relative_id=rel.id)
