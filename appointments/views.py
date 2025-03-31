from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, viewsets
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from appointments.models import Appointment
from appointments.serializers import AppointmentBookingSerializer, AppointmentListSerializer
from patients.models import Patient
from professionals.helpers import generate_slots
from professionals.models import Professional
from professionals.serializers import ServiceSlotSerializer
from django.utils.timezone import now
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class AvailableSlotsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AvailableSlotsView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Retrieve available appointment slots based on service and date range.",
        manual_parameters=[
            openapi.Parameter(
                name="services",
                in_=openapi.IN_QUERY,
                description="List of service IDs. Can be repeated (e.g., ?services=1&services=2)",
                required=True,
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_INTEGER),
                collection_format="multi"
            ),
            openapi.Parameter(
                name="start_date",
                in_=openapi.IN_QUERY,
                description="Start date in YYYY-MM-DD format",
                required=True,
                type=openapi.TYPE_STRING,
                format="date"
            ),
            openapi.Parameter(
                name="end_date",
                in_=openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format",
                required=True,
                type=openapi.TYPE_STRING,
                format="date"
            ),
        ],
        responses={200: ServiceSlotSerializer(many=True)}
    )
    def get(self, request):
        service_ids = request.query_params.getlist("services", [])
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        return self.fetch_slots(request, service_ids, start_date, end_date)

    def fetch_slots(self, request, service_ids, start_date, end_date):
        if not service_ids or not start_date or not end_date:
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        current_datetime = now()
        today = current_datetime.date()
        current_time = current_datetime.time()

        if end_date < today:
            return Response({"error": "End date cannot be in the past."}, status=status.HTTP_400_BAD_REQUEST)

        if start_date < today:
            start_date = today

        if start_date > end_date:
            return Response({"error": "Start date cannot be after end date."}, status=status.HTTP_400_BAD_REQUEST)

        available_slots = []
        current_date = start_date

        while current_date <= end_date:
            all_slots = generate_slots(service_ids, current_date)

            booked_slots = set(
                (appt.professional.id, appt.scheduled_to.date(), appt.scheduled_to.time())
                for appt in Appointment.objects.filter(service_id__in=service_ids)
                .exclude(status="CANCELED")
            )

            filtered_slots = []

            for slot in all_slots:
                is_booked = (
                    slot["professional"]["id"],
                    current_date,
                    slot["start_time"]
                ) in booked_slots

                # Skip booked or past slots (if today, only future times allowed)
                if is_booked:
                    continue
                if current_date == today and slot["start_time"] <= current_time:
                    continue

                slot["date"] = current_date
                filtered_slots.append(slot)

            available_slots.extend(filtered_slots)
            current_date += timedelta(days=1)

        available_slots = sorted(available_slots, key=lambda s: (s["date"], s["start_time"]))

        paginator = AvailableSlotsPagination()
        paginated = paginator.paginate_queryset(available_slots, request)
        serializer = ServiceSlotSerializer(paginated, many=True)

        return paginator.get_paginated_response(serializer.data)


class AppointmentBookingView(generics.CreateAPIView):
    serializer_class = AppointmentBookingSerializer
    queryset = Appointment.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Book an appointment using a shift ID and appointment time.",
        request_body=AppointmentBookingSerializer,
        responses={201: AppointmentListSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AppointmentActionViewSet(viewsets.GenericViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentListSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.get_queryset().filter(id=self.kwargs["pk"]).first()

    def is_doctor(self, user, appointment):
        return Professional.objects.filter(user_ptr_id=user.id, id=appointment.professional_id).exists()

    def is_patient(self, user, appointment):
        return Patient.objects.filter(user_ptr_id=user.id, pid=appointment.patient_id).exists()

    def perform_status_transition(self, request, pk, new_status, allowed_roles):
        appointment = self.get_object()
        if not appointment:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        # ⛔ permission check
        user = request.user
        role_check = {
            "doctor": self.is_doctor(user, appointment),
            "patient": self.is_patient(user, appointment),
        }

        if not any(role_check[role] for role in allowed_roles):
            raise PermissionDenied("You are not allowed to perform this action.")

        # ✅ transition
        try:
            appointment.update_status(new_status, changed_by=request.user)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AppointmentListSerializer(appointment).data)

    @swagger_auto_schema(
        operation_description="Confirm an appointment (doctor only).",
        responses={200: AppointmentListSerializer}
    )
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self.perform_status_transition(request, pk, "CONFIRMED", allowed_roles=["doctor"])

    @swagger_auto_schema(
        operation_description="Initiate an appointment (doctor only).",
        responses={200: AppointmentListSerializer}
    )
    @action(detail=True, methods=["post"])
    def initiate(self, request, pk=None):
        return self.perform_status_transition(request, pk, "INITIATED", allowed_roles=["doctor"])

    @swagger_auto_schema(
        operation_description="Mark the appointment as completed (doctor only).",
        responses={200: AppointmentListSerializer}
    )
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self.perform_status_transition(request, pk, "COMPLETED", allowed_roles=["doctor"])

    @swagger_auto_schema(
        operation_description="Cancel the appointment (doctor or patient).",
        responses={200: AppointmentListSerializer}
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self.perform_status_transition(request, pk, "CANCELED", allowed_roles=["doctor", "patient"])
