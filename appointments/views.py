from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, viewsets
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta, time
from appointments.models import Appointment
from appointments.serializers import AppointmentBookingSerializer, AppointmentListSerializer
from patients.models import Patient
from professionals.models import Professional, ServiceSlot
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from django.db.models import OuterRef, Exists
from drf_yasg import openapi
from django.utils import timezone


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
                description="Start date in YYYY-MM-DD format. Defaults to now when omitted.",
                required=False,
                type=openapi.TYPE_STRING,
                format="date"
            ),
            openapi.Parameter(
                name="end_date",
                in_=openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format. Defaults to 30 days from the start date when omitted.",
                required=False,
                type=openapi.TYPE_STRING,
                format="date"
            ),
        ],
        responses={
            200: openapi.Response(
                "Available slots",
                # You can adjust or omit the serializer here if it's not needed.
                # ServiceSlotSerializer(many=True),
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
                                "professional_id": 12,
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
        start_param = request.query_params.get("start_date")
        end_param = request.query_params.get("end_date")

        if not service_ids:
            return Response({"error": "Missing required services parameter."}, status=status.HTTP_400_BAD_REQUEST)

        now_dt = timezone.now()
        current_tz = timezone.get_current_timezone()

        try:
            if start_param:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").date()
                start_date_dt = timezone.make_aware(datetime.combine(start_date, time.min), current_tz)
            else:
                start_date_dt = now_dt

            start_date_dt = max(start_date_dt, now_dt)

            if end_param:
                end_date = datetime.strptime(end_param, "%Y-%m-%d").date()
                end_date_dt = timezone.make_aware(datetime.combine(end_date, time.max), current_tz)
            else:
                default_end_date = (start_date_dt + timedelta(days=30)).date()
                end_date_dt = timezone.make_aware(datetime.combine(default_end_date, time.max), current_tz)
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if end_date_dt < now_dt:
            return Response({"error": "End date cannot be in the past."}, status=status.HTTP_400_BAD_REQUEST)

        start_date_dt = max(start_date_dt, now_dt)
        if end_date_dt < start_date_dt:
            return Response({"error": "end_date must be on or after start_date."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter all slots within range and services
        service_slots = ServiceSlot.objects.filter(
            shift__service_id__in=service_ids,
            start_time__gte=start_date_dt,
            start_time__lte=end_date_dt
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

        # Build doctors map (unique professionals in results)
        doctor_map = {}
        results = []
        for slot in paginated_slots:
            pro = slot.shift.professional
            service = slot.shift.service

            # Compose slot dict
            slot_dict = {
                "id": slot.id,
                "shift_id": slot.shift.id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "professional_id": pro.id,
                "service": {
                    "id": service.id,
                    "name": service.name,
                },
            }
            results.append(slot_dict)

            # Add professional to doctor map if not already present
            if pro.id not in doctor_map:
                doctor_map[pro.id] = {
                    "id": pro.id,
                    "first_name": pro.first_name,
                    "last_name": pro.last_name,
                    "email": pro.email,
                    "avatar": pro.avatar.url if getattr(pro, "avatar", None) and pro.avatar and hasattr(pro.avatar, "url") else None,
                }

        # Build paginated response manually since we bypassed the serializer
        response = paginator.get_paginated_response(results)
        response.data["professionals"] = list(doctor_map.values())
        return response


class AvailableSpecializationsView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="List specializations that have available slots within a date range.",
        manual_parameters=[
            openapi.Parameter(
                name="start_date",
                in_=openapi.IN_QUERY,
                description="Start date in YYYY-MM-DD format. Defaults to now when omitted with end_date.",
                required=False,
                type=openapi.TYPE_STRING,
                format="date"
            ),
            openapi.Parameter(
                name="end_date",
                in_=openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format. Defaults to 30 days from now when omitted with start_date.",
                required=False,
                type=openapi.TYPE_STRING,
                format="date"
            ),
        ],
        responses={
            200: openapi.Response(
                "Available specializations with up to four upcoming slots each",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Dermatology",
                            "slots": [
                                {
                                    "slot_id": 10,
                                    "shift_id": 3,
                                    "start_time": "2025-06-01T10:00:00Z",
                                    "end_time": "2025-06-01T10:30:00Z",
                                    "service_id": 2,
                                    "doctor": {
                                        "id": 5,
                                        "first_name": "Ana",
                                        "last_name": "Silva",
                                        "email": "ana@example.com",
                                        "avatar": None
                                    }
                                }
                            ]
                        }
                    ]
                }
            ),
            400: "Invalid or missing parameters"
        }
    )
    def get(self, request):
        start_param = request.query_params.get("start_date")
        end_param = request.query_params.get("end_date")

        now_dt = timezone.now()
        if start_param and end_param:
            try:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_param, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            start_dt = timezone.make_aware(datetime.combine(start_date, time.min), timezone.get_current_timezone())
            end_dt = timezone.make_aware(datetime.combine(end_date, time.max), timezone.get_current_timezone())
        elif not start_param and not end_param:
            start_dt = now_dt
            end_dt = now_dt + timedelta(days=30)
        else:
            return Response({"error": "Provide both start_date and end_date or neither."}, status=status.HTTP_400_BAD_REQUEST)

        if end_dt < start_dt:
            return Response({"error": "end_date must be on or after start_date."}, status=status.HTTP_400_BAD_REQUEST)

        start_dt = max(start_dt, now_dt)

        # Find slots in the window that are not booked (except by canceled appointments)
        service_slots = ServiceSlot.objects.filter(
            shift__professional__specializations__isnull=False,
            start_time__gte=start_dt,
            start_time__lte=end_dt,
        ).distinct()

        active_appointments = Appointment.objects.filter(service_slot=OuterRef("pk")).exclude(status="CANCELED")
        service_slots = (
            service_slots.annotate(is_booked=Exists(active_appointments))
            .filter(is_booked=False)
            .select_related("shift__professional", "shift__service")
            .prefetch_related("shift__professional__specializations")
            .order_by("start_time")
        )

        specialization_map = {}
        doctor_cache = {}

        for slot in service_slots:
            professional = slot.shift.professional
            if professional.id not in doctor_cache:
                doctor_cache[professional.id] = {
                    "id": professional.id,
                    "first_name": professional.first_name,
                    "last_name": professional.last_name,
                    "email": professional.email,
                    "avatar": professional.avatar.url if getattr(professional, "avatar", None) and professional.avatar and hasattr(professional.avatar, "url") else None,
                }

            slot_payload = {
                "slot_id": slot.id,
                "shift_id": slot.shift_id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "service_id": slot.shift.service_id,
                "doctor": doctor_cache[professional.id],
            }

            for specialization in professional.specializations.all():
                entry = specialization_map.setdefault(
                    specialization.id, {"id": specialization.id, "name": specialization.name, "slots": []}
                )
                if len(entry["slots"]) < 4:
                    entry["slots"].append(slot_payload)

        return Response(list(specialization_map.values()))


class AvailableProfessionalsView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="List professionals that have available slots within a date range.",
        manual_parameters=[
            openapi.Parameter(
                name="start_date",
                in_=openapi.IN_QUERY,
                description="Start date in YYYY-MM-DD format. Defaults to now when omitted with end_date.",
                required=False,
                type=openapi.TYPE_STRING,
                format="date",
            ),
            openapi.Parameter(
                name="end_date",
                in_=openapi.IN_QUERY,
                description="End date in YYYY-MM-DD format. Defaults to 30 days from now when omitted with start_date.",
                required=False,
                type=openapi.TYPE_STRING,
                format="date",
            ),
        ],
        responses={
            200: openapi.Response(
                "Available professionals with up to four upcoming slots each",
                examples={
                    "application/json": [
                        {
                            "id": 5,
                            "first_name": "Alex",
                            "last_name": "Silva",
                            "email": "alex@example.com",
                            "avatar": None,
                            "slots": [
                                {
                                    "slot_id": 10,
                                    "shift_id": 3,
                                    "start_time": "2025-06-01T10:00:00Z",
                                    "end_time": "2025-06-01T10:30:00Z",
                                    "service_id": 2,
                                }
                            ],
                        }
                    ]
                },
            ),
            400: "Invalid or missing parameters",
        },
    )
    def get(self, request):
        start_param = request.query_params.get("start_date")
        end_param = request.query_params.get("end_date")

        now_dt = timezone.now()
        if start_param and end_param:
            try:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_param, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

            start_dt = timezone.make_aware(datetime.combine(start_date, time.min), timezone.get_current_timezone())
            end_dt = timezone.make_aware(datetime.combine(end_date, time.max), timezone.get_current_timezone())
        elif not start_param and not end_param:
            start_dt = now_dt
            end_dt = now_dt + timedelta(days=30)
        else:
            return Response({"error": "Provide both start_date and end_date or neither."}, status=status.HTTP_400_BAD_REQUEST)

        if end_dt < start_dt:
            return Response({"error": "end_date must be on or after start_date."}, status=status.HTTP_400_BAD_REQUEST)

        start_dt = max(start_dt, now_dt)

        active_appointments = Appointment.objects.filter(service_slot=OuterRef("pk")).exclude(status="CANCELED")
        service_slots = (
            ServiceSlot.objects.filter(start_time__gte=start_dt, start_time__lte=end_dt)
            .annotate(is_booked=Exists(active_appointments))
            .filter(is_booked=False)
            .select_related("shift__professional", "shift__service")
            .order_by("start_time")
        )

        professional_map = {}

        for slot in service_slots:
            professional = slot.shift.professional
            entry = professional_map.setdefault(
                professional.id,
                {
                    "id": professional.id,
                    "first_name": professional.first_name,
                    "last_name": professional.last_name,
                    "email": professional.email,
                    "avatar": professional.avatar.url if getattr(professional, "avatar", None) and professional.avatar and hasattr(professional.avatar, "url") else None,
                    "slots": [],
                },
            )

            if len(entry["slots"]) >= 4:
                continue

            entry["slots"].append(
                {
                    "slot_id": slot.id,
                    "shift_id": slot.shift_id,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "service_id": slot.shift.service_id,
                }
            )

        return Response(list(professional_map.values()))


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
        if not user:
            return False
        professional = appointment.professional
        return user.id in {professional.user_ptr_id, professional.id}

    def is_patient(self, user, appointment):
        if not user:
            return False
        patient = appointment.patient
        return user.id in {patient.user_ptr_id, patient.pid}

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
