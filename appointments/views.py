from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import datetime, timedelta
from doctors.helpers import generate_slots
from doctors.serializers import ServiceSlotSerializer
from .models import Appointment


class AvailableSlotsView(APIView):
    """
    API View to return available slots for a given service, excluding booked slots.
    """
    permission_classes = [permissions.AllowAny]  # Public access for now

    def get(self, request):
        """
        Allows fetching available slots using GET request with query parameters.
        """
        service_ids = request.query_params.getlist("services", [])
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        return self.fetch_slots(service_ids, start_date, end_date)

    def fetch_slots(self, service_ids, start_date, end_date):
        """
        Shared logic for both GET and POST requests.
        """
        if not service_ids:
            return Response({"error": "Service IDs are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not start_date or not end_date:
            return Response({"error": "Start date and end date are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({"error": "Start date cannot be after end date."}, status=status.HTTP_400_BAD_REQUEST)

        available_slots = []

        # Generate slots for each date in the range
        current_date = start_date
        while current_date <= end_date:
            all_slots = generate_slots(service_ids, current_date)  # ✅ Already dictionaries

            # Get booked appointment slots (excluding cancelled ones)
            booked_slots = set(
                (appt.doctor.id, appt.scheduled_to.date(), appt.scheduled_to.time())
                for appt in Appointment.objects.filter(service_id__in=service_ids)
                .exclude(status="cancelled")
            )

            # Filter out booked slots
            filtered_slots = [
                slot for slot in all_slots if (
                    slot["doctor"]["id"], current_date, slot["start_time"]) not in booked_slots
            ]

            available_slots.extend(filtered_slots)
            current_date += timedelta(days=1)

        # ✅ Use the serializer to format response properly
        serializer = ServiceSlotSerializer(available_slots, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
