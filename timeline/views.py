from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

from timeline.serializers import TimelineItemSerializer
from timeline.timeline_helper import TimelineItem


class TimelinePagination(PageNumberPagination):
    page_size = 10


class PatientTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Professionals get empty list
        if hasattr(user, 'doctor') or hasattr(user, 'professional'):
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            })

        # Collect timeline items (example with appointments)
        timeline_items = []

        now = timezone.now()

        # Example: Appointments
        appointments = user.patient.appointments.filter(status__in=["CONFIRMED", "INITIATED", "COMPLETED"])
        for appt in appointments:
            item = TimelineItem(
                type="appointment",
                title=f"Appointment with Dr. {appt.professional.full_name}",
                when=appt.scheduled_to,
                is_future=appt.scheduled_to > now,
                reference_id=str(appt.id)
            )
            timeline_items.append(item)

        # You could add medications, reminders, lab results, etc. in a similar way here.

        # Sort items by 'when'
        timeline_items.sort(key=lambda x: x.when)

        # Serialize and paginate
        serializer = TimelineItemSerializer(timeline_items, many=True)
        paginator = TimelinePagination()
        paginated_items = paginator.paginate_queryset(serializer.data, request)

        return paginator.get_paginated_response(paginated_items)
