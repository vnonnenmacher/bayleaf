# events/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class BaseEvent(models.Model):
    """
    Concrete base model for all system events (appointments, med reminders, etc.).
    Child models will use Django multi-table inheritance (OneToOne to this row).
    Query your global timeline with: BaseEvent.objects.all()
    """

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        CONFIRMED = "CONFIRMED", "Confirmed"
        INITIATED = "INITIATED", "Initiated"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"
        RESCHEDULED = "RESCHEDULED", "Rescheduled"

    # Allowed transitions (enforced in update_status)
    VALID_TRANSITIONS = {
        Status.REQUESTED: [Status.CONFIRMED, Status.CANCELED],
        Status.CONFIRMED: [Status.INITIATED, Status.CANCELED, Status.RESCHEDULED],
        Status.INITIATED: [Status.COMPLETED, Status.CANCELED],
        Status.COMPLETED: [],
        Status.CANCELED: [],
        Status.RESCHEDULED: [Status.CONFIRMED],  # must confirm the rescheduled instance
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Helpful discriminator for quick filters and downstream analytics
    # e.g. "appointment", "take_medication_event"
    event_type = models.CharField(max_length=50, blank=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_events",
        db_index=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )

    # If this event was superseded by another (reschedule flow):
    rescheduled_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rescheduled_from",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "status"]),
            models.Index(fields=["created_by", "created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type or self.__class__.__name__} [{self.status}] by {self.created_by_id} @ {self.created_at:%Y-%m-%d %H:%M}"

    # ---------- Lifecycle helpers ----------

    def save(self, *args, **kwargs):
        # Auto-fill event_type with the concrete child class name if not set
        if not self.event_type:
            self.event_type = self.__class__.__name__.lower()
        super().save(*args, **kwargs)

    def validate_status_transition(self, new_status: str) -> None:
        current = self.status
        allowed = self.VALID_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid status transition: {current} → {new_status}")

    def update_status(self, new_status: str, changed_by=None) -> None:
        if new_status == self.status:
            return  # no-op

        self.validate_status_transition(new_status)

        # Persist change first so history captures the new truth even if signal/other logic runs
        previous = self.status
        self.status = new_status
        self.save(update_fields=["status"])

        EventStatusHistory.objects.create(
            event=self,
            event_type=self.event_type,
            previous_status=previous,
            new_status=new_status,
            changed_by=changed_by,
        )

    def mark_rescheduled(self, new_event: "BaseEvent", changed_by=None) -> None:
        """
        Link this event to a new one and set status to RESCHEDULED.
        The new_event should typically be the replacement (same user/patient context).
        """
        self.rescheduled_to = new_event
        self.save(update_fields=["rescheduled_to"])
        self.update_status(self.Status.RESCHEDULED, changed_by=changed_by)


class EventStatusHistory(models.Model):
    """
    Immutable audit log of status changes.
    """
    event = models.ForeignKey(
        BaseEvent, on_delete=models.CASCADE, related_name="status_history", db_index=True
    )
    event_type = models.CharField(max_length=50, blank=True)  # snapshot for convenience
    previous_status = models.CharField(max_length=20, choices=BaseEvent.Status.choices)
    new_status = models.CharField(max_length=20, choices=BaseEvent.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_status_changes",
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [models.Index(fields=["event_type", "new_status", "changed_at"])]

    def __str__(self):
        return f"{self.event_type or 'event'}: {self.previous_status} → {self.new_status} @ {self.changed_at:%Y-%m-%d %H:%M}"


# ---------- Abstract specializations (keep abstract!) ----------

class ScheduledCheckpointEvent(BaseEvent):
    """
    Events that must be completed within a time window (no duration).
    Examples: take medication dose between X and Y.
    """
    scheduled_to_complete_from = models.DateTimeField(db_index=True)
    scheduled_to_complete_until = models.DateTimeField(db_index=True)

    class Meta:
        abstract = True
        ordering = ["scheduled_to_complete_from"]

    def is_within_timeframe(self) -> bool:
        now = timezone.now()
        return self.scheduled_to_complete_from <= now <= self.scheduled_to_complete_until

    def mark_completed(self, changed_by=None) -> None:
        if not self.is_within_timeframe():
            raise ValueError("Cannot complete outside scheduled window.")
        self.update_status(BaseEvent.Status.COMPLETED, changed_by=changed_by)


class ScheduledTimedEvent(BaseEvent):
    """
    Events that start at a time and have a duration.
    Examples: appointments, scheduled calls, procedures.
    """
    scheduled_to = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField()

    class Meta:
        abstract = True
        ordering = ["scheduled_to"]

    def get_end_time(self):
        return self.scheduled_to + timezone.timedelta(minutes=self.duration_minutes)

    def mark_completed(self, changed_by=None) -> None:
        self.update_status(BaseEvent.Status.COMPLETED, changed_by=changed_by)

class ScheduledDueWindowEvent(BaseEvent):
    """
    An event that must be completed anytime between a start and end datetime.
    Unlike ScheduledTimedEvent, it has no duration — only a completion window.
    Example: take a medication anytime between 08:00–12:00.
    """
    due_from = models.DateTimeField(db_index=True, default=None)
    due_until = models.DateTimeField(db_index=True, default=None)

    class Meta:
        abstract = True
        ordering = ["due_from"]

    def is_within_window(self) -> bool:
        now = timezone.now()
        return self.due_from <= now <= self.due_until

    def mark_completed(self, changed_by=None):
        if not self.is_within_window():
            raise ValueError("Cannot complete outside due window.")
        self.update_status(BaseEvent.Status.COMPLETED, changed_by=changed_by)
