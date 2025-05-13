from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination


from appointments.models import Appointment
from appointments.serializers import AppointmentListSerializer
from patients.permissions import IsPatient
from .serializers import PatientSerializer
from .models import Patient
from django.utils.timezone import now

from appointments.filters import apply_appointment_filters
from rest_framework.response import Response
from professionals.models import Professional
from professionals.serializers import ProfessionalListSerializer


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


class PatientUpdateView(generics.RetrieveUpdateAPIView):
    """API endpoint for patients to update their Address & Contact details."""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve the logged-in user's Patient profile correctly."""
        user = self.request.user  # Get the authenticated user

        # Ensure the user is actually a Patient
        try:
            return Patient.objects.get(user_ptr_id=user.id)  # ✅ Correct lookup
        except Patient.DoesNotExist:
            raise Patient.DoesNotExist("The logged-in user is not a registered patient.")


class PatientListView(generics.ListAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]  # Customize this as needed

    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']


class PatientAppointmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            patient = Patient.objects.get(user_ptr_id=request.user.id)
        except Patient.DoesNotExist:
            return Response({"appointments": [], "professionals": []})

        qs = Appointment.objects.filter(patient=patient)
        appointments = apply_appointment_filters(qs, request).order_by("-scheduled_to")

        # ✅ Apply pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10  # or set page_size_query_param = "page_size" for dynamic size

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
