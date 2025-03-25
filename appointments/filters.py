from datetime import datetime
from django.utils.timezone import make_aware


def apply_appointment_filters(queryset, request):
    service = request.query_params.get("service")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    if service:
        queryset = queryset.filter(service_id=service)

    if start_date:
        try:
            start_dt = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
            queryset = queryset.filter(scheduled_to__gte=start_dt)
        except ValueError:
            pass  # Optionally: raise a 400 error

    if end_date:
        try:
            end_dt = make_aware(datetime.strptime(end_date, "%Y-%m-%d"))
            queryset = queryset.filter(scheduled_to__lte=end_dt)
        except ValueError:
            pass

    return queryset
