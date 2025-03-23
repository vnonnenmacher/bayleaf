from datetime import datetime, timedelta
from .models import Shift


def generate_slots(service_ids, date):
    """
    Generate available slots based on shifts and slot duration for a given date.

    Args:
        service_ids (list[int]): List of service IDs to generate slots for.
        date (datetime.date): The specific date for which slots should be generated.

    Returns:
        list[dict]: List of available slots serialized into JSON-compatible format.
    """
    slots = []

    # Get all shifts that match the given service IDs and weekday
    weekday = date.weekday()  # Convert the date into a weekday index
    shifts = Shift.objects.filter(service_id__in=service_ids, weekday=weekday).select_related("professional", "service")

    for shift in shifts:
        # Convert shift times into datetime objects for calculation
        current_time = datetime.combine(date, shift.from_time)
        end_time = datetime.combine(date, shift.to_time)
        slot_duration = timedelta(minutes=shift.slot_duration)

        # Generate slots within the shift's time range
        while current_time + slot_duration <= end_time:
            slot_instance = {
                "doctor": {
                    "id": shift.professional.id,
                    "first_name": shift.professional.first_name,
                    "last_name": shift.professional.last_name,
                    "email": shift.professional.email
                },
                "service_id": shift.service.id,
                "start_time": current_time.time(),
                "end_time": (current_time + slot_duration).time()
            }
            slots.append(slot_instance)
            current_time += slot_duration  # Move to the next slot

    return slots  # ✅ Now returning a list of dictionaries
