import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class BaseEvent(models.Model):
    """
    Abstract base model for system events (e.g., Appointments, Medication Reminders).
    Tracks status transitions and history.
    """

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("CONFIRMED", "Confirmed"),
        ("INITIATED", "Initiated"),
        ("COMPLETED", "Completed"),
        ("CANCELED", "Canceled"),
        ("RESCHEDULED", "Rescheduled"),
    ]

    VALID_TRANSITIONS = {
        "REQUESTED": ["CONFIRMED", "CANCELED"],
        "CONFIRMED": ["INITIATED", "CANCELED", "RESCHEDULED"],
        "INITIATED": ["COMPLETED", "CANCELED"],
        "COMPLETED": [],
        "CANCELED": [],
        "RESCHEDULED": ["CONFIRMED"],  # Rescheduled events must be confirmed again
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_created_events"  # dynamic reverse relation
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="REQUESTED")

    rescheduled_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="rescheduled_from"
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]  # Latest events first

    def __str__(self):
        return f"{self.event_type} - {self.status} by {self.created_by.email} at {self.created_at}"

    def validate_status_transition(self, new_status):
        """
        Validates if the transition from the current status to `new_status` is allowed.
        """
        if new_status not in self.VALID_TRANSITIONS[self.status]:
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}.")

    def update_status(self, new_status, changed_by=None):
        """Updates the status and logs the change in `EventStatusHistory`."""
        if new_status == self.status:
            return  # No change

        self.validate_status_transition(new_status)

        # Log status change
        EventStatusHistory.objects.create(
            event_id=self.id,  # Store UUID instead of ForeignKey
            event_type=self.__class__.__name__,  # Store event model name
            previous_status=self.status,
            new_status=new_status,
            changed_by=changed_by,
        )

        # Update event status
        self.status = new_status
        self.save()


class EventStatusHistory(models.Model):
    """
    Tracks the history of status changes for events.
    """
    event_id = models.UUIDField()  # Store event's UUID without ForeignKey
    event_type = models.CharField(max_length=50)  # Store event type (for reference)
    previous_status = models.CharField(max_length=20, choices=BaseEvent.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=BaseEvent.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_changes"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.event_type} - {self.previous_status} → {self.new_status} by {self.changed_by} on {self.changed_at}"


class ScheduledCheckpointEvent(BaseEvent):
    """
    Abstract model for scheduled events that do not have a duration.
    Examples: Taking medication, entering emergency room, marking a check-in.
    """

    scheduled_to_complete_from = models.DateTimeField()
    scheduled_to_complete_until = models.DateTimeField()

    class Meta:
        abstract = True
        ordering = ["scheduled_to_complete_from"]

    def is_within_timeframe(self):
        """Returns True if the event is currently within the scheduled timeframe."""
        now = timezone.now()
        return self.scheduled_to_complete_from <= now <= self.scheduled_to_complete_until

    def mark_completed(self):
        """Marks the checkpoint event as completed."""
        if not self.is_within_timeframe():
            raise ValueError("Cannot complete event outside its scheduled timeframe.")
        self.update_status("COMPLETED")


class ScheduledTimedEvent(BaseEvent):
    """
    Abstract model for scheduled events that have a defined start time and duration.
    Examples: Appointments, scheduled activities.
    """

    scheduled_to = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()

    class Meta:
        abstract = True
        ordering = ["scheduled_to"]

    def get_end_time(self):
        """Returns the calculated end time of the event."""
        return self.scheduled_to + timezone.timedelta(minutes=self.duration_minutes)

    def mark_completed(self):
        """Marks the event as completed."""
        self.update_status("COMPLETED")
