# careplans/services/event_generator.py
from datetime import datetime, timedelta
from django.utils import timezone
from dateutil.rrule import rrule, DAILY, WEEKLY

from careplans.models import (
    CarePlanAction,
    CarePlanActivityEvent,
    ActionCategory,
)


def generate_events_for_action(action: CarePlanAction):
    """
    Expand a CarePlanAction into concrete CarePlanActivityEvent rows.

    Scheduling priority:
        1) action.schedule_json  (ALWAYS used)
        2) category-specific detail overrides
        3) careplan.start_date baseline

    Supported schedule_json patterns:
        - {"on_start": true}
        - {"frequency": "DAILY", "at_time": "08:00", "duration_days": 30}
        - {"frequency": "WEEKLY", "weekdays": ["MON","WED"], "at_time": "08:00"}
        - {"interval_hours": 6, "duration_days": 5}
        - {"times_per_day": 3, "at_times": ["08:00","14:00","20:00"], "duration_days": 10}
        - Appointment-style: {"preferred_window_start": "...", "preferred_window_end": "..."}
    """

    schedule = action.schedule_json or {}
    plan = action.careplan

    # Professional *is* the user (multi-table inheritance)
    owner_user = plan.owner if plan.owner else None

    start_date = plan.start_date or timezone.now().date()
    start_dt = timezone.make_aware(
        datetime.combine(start_date, datetime.min.time())
    )
    now = timezone.now()

    # -------------------------------------------------------------------------
    # 0. Remove existing events (safe & predictable)
    # -------------------------------------------------------------------------
    CarePlanActivityEvent.objects.filter(action=action).delete()

    # -------------------------------------------------------------------------
    # 1. ONE-TIME on_start
    # -------------------------------------------------------------------------
    if schedule.get("on_start") is True:
        CarePlanActivityEvent.objects.create(
            action=action,
            due_from=now,
            due_until=now + timedelta(hours=12),
            description=action.title,
            created_by=owner_user,
        )
        return

    # Extract main schedule fields
    frequency = schedule.get("frequency", "").upper()
    at_time = schedule.get("at_time", "08:00")
    duration_days = schedule.get("duration_days")

    # Medication detail override
    med = getattr(action, "medication_detail", None)
    if med:
        if med.duration_days:
            duration_days = med.duration_days
        if med.frequency:
            frequency = med.frequency.upper()

    if not duration_days:
        duration_days = 1

    # Pure helper to parse HH:MM
    def parse_time(t):
        hour, minute = map(int, t.split(":"))
        return datetime.strptime(t, "%H:%M").replace(hour=hour, minute=minute).time()

    # -------------------------------------------------------------------------
    # 2. DAILY
    # -------------------------------------------------------------------------
    if frequency == "DAILY":
        time_obj = parse_time(at_time)

        for i in range(duration_days):
            date = start_date + timedelta(days=i)
            due_dt = timezone.make_aware(
                datetime.combine(date, time_obj)
            )

            CarePlanActivityEvent.objects.create(
                action=action,
                due_from=due_dt,
                due_until=due_dt + timedelta(hours=4),
                description=action.title,
                created_by=owner_user,
            )
        return

    # -------------------------------------------------------------------------
    # 3. WEEKLY
    # -------------------------------------------------------------------------
    if frequency == "WEEKLY":
        weekdays = schedule.get("weekdays", [])  # e.g. ["MON","WED"]
        if not weekdays:
            return

        weekday_map = {
            "MON": 0, "TUE": 1, "WED": 2,
            "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6
        }

        time_obj = parse_time(at_time)
        end_date = start_date + timedelta(days=duration_days)

        rr = rrule(
            WEEKLY,
            dtstart=start_dt,
            until=datetime.combine(end_date, datetime.min.time()),
            byweekday=[weekday_map[d] for d in weekdays if d in weekday_map],
        )

        for occur in rr:
            due_dt = timezone.make_aware(
                datetime.combine(occur.date(), time_obj)
            )

            CarePlanActivityEvent.objects.create(
                action=action,
                due_from=due_dt,
                due_until=due_dt + timedelta(hours=4),
                description=action.title,
                created_by=owner_user,
            )
        return

    # -------------------------------------------------------------------------
    # 4. INTERVAL: every X hours
    # -------------------------------------------------------------------------
    interval_hours = schedule.get("interval_hours")
    if interval_hours:
        end_dt = start_dt + timedelta(days=duration_days)
        cursor = start_dt

        while cursor <= end_dt:
            CarePlanActivityEvent.objects.create(
                action=action,
                due_from=cursor,
                due_until=cursor + timedelta(hours=2),
                description=action.title,
                created_by=owner_user,
            )
            cursor += timedelta(hours=interval_hours)
        return

    # -------------------------------------------------------------------------
    # 5. MULTIPLE TIMES PER DAY
    # -------------------------------------------------------------------------
    times_per_day = schedule.get("times_per_day")
    at_times = schedule.get("at_times")   # e.g. ["08:00","14:00","20:00"]

    if times_per_day and at_times:
        for d in range(duration_days):
            current_date = start_date + timedelta(days=d)
            for t in at_times:
                time_obj = parse_time(t)
                due_dt = timezone.make_aware(
                    datetime.combine(current_date, time_obj)
                )
                CarePlanActivityEvent.objects.create(
                    action=action,
                    due_from=due_dt,
                    due_until=due_dt + timedelta(hours=2),
                    description=action.title,
                    created_by=owner_user,
                )
        return

    # -------------------------------------------------------------------------
    # 6. APPOINTMENT (from appointment_detail)
    # -------------------------------------------------------------------------
    if action.category == ActionCategory.APPOINTMENT:
        appt = getattr(action, "appointment_detail", None)
        if appt and appt.preferred_window_start:
            CarePlanActivityEvent.objects.create(
                action=action,
                due_from=appt.preferred_window_start,
                due_until=appt.preferred_window_end
                    or (appt.preferred_window_start + timedelta(hours=1)),
                description=action.title,
                created_by=owner_user,
            )
        return

    # -------------------------------------------------------------------------
    # 7. SAFE NO-OP fallback
    # -------------------------------------------------------------------------
    return
