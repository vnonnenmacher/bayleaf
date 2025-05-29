from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, viewsets
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from appointments.models import Appointment
from appointments.serializers import AppointmentBookingSerializer, AppointmentListSerializer
from patients.models import Patient
from professionals.models import Professional, ServiceSlot
from professionals.serializers import ProfessionalMiniSerializer, ServiceSlotSerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from django.db.models import OuterRef, Exists
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
        responses={
            200: openapi.Response(
                "Available slots",
                ServiceSlotSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 2,
                        "next": None,
                        "previous": None,
                        "results": [
                            {
                                "id": 123,
                                "shift_id": 5,
                                "start_time": "2025-06-01T10:00:00Z",
                                "end_time": "2025-06-01T10:30:00Z",
                                "professional": {
                                    "id": 12,
                                    "first_name": "Ana",
                                    "last_name": "Silva",
                                    "email": "ana@domain.com",
                                    "avatar": "https://cdn.../avatar.png"
                                },
                                "service": {
                                    "id": 2,
                                    "name": "Cardiology"
                                }
                            }
                        ],
                        "doctors": [
                            {
                                "id": 12,
                                "first_name": "Ana",
                                "last_name": "Silva",
                                "email": "ana@domain.com",
                                "avatar": "https://cdn.../avatar.png"
                            }
                        ]
                    }
                }
            ),
            400: "Invalid or missing parameters"
        }
    )
    def get(self, request):
        service_ids = request.query_params.getlist("services", [])
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not service_ids or not start_date or not end_date:
            return Response({"error": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # inclusive
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        now_dt = datetime.now()
        if end_date_dt.date() < now_dt.date():
            return Response({"error": "End date cannot be in the past."}, status=status.HTTP_400_BAD_REQUEST)
        if start_date_dt.date() < now_dt.date():
            start_date_dt = now_dt

        # Filter all slots within range and services
        service_slots = ServiceSlot.objects.filter(
            shift__service_id__in=service_ids,
            start_time__gte=start_date_dt,
            start_time__lt=end_date_dt
        )

        # Exclude slots with active appointments (not canceled)
        active_appointments = Appointment.objects.filter(
            service_slot=OuterRef('pk')
        ).exclude(status="CANCELED")
        service_slots = service_slots.annotate(
            is_booked=Exists(active_appointments)
        ).filter(is_booked=False)

        # Only in the future
        service_slots = service_slots.filter(start_time__gte=now_dt)

        # Paginate
        paginator = AvailableSlotsPagination()
        paginated_slots = paginator.paginate_queryset(service_slots, request)

        # Serialize
        slot_serializer = ServiceSlotSerializer(paginated_slots, many=True)

        # Build doctors map (unique professionals in results)
        doctor_map = {}
        for slot in paginated_slots:
            pro = slot.shift.professional
            if pro.id not in doctor_map:
                doctor_map[pro.id] = ProfessionalMiniSerializer(pro).data

        response = paginator.get_paginated_response(slot_serializer.data)
        response.data["doctors"] = list(doctor_map.values())
        return response


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
