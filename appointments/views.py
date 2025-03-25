from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from appointments.models import Appointment
from appointments.serializers import AppointmentBookingSerializer
from professionals.helpers import generate_slots
from professionals.serializers import ServiceSlotSerializer
from django.utils.timezone import now


class AvailableSlotsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AvailableSlotsView(APIView):
    permission_classes = [permissions.AllowAny]

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
