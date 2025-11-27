# careplans/models.py
from __future__ import annotations

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# ---- External models you already have in Bayleaf ----
from patients.models import Patient
from professionals.models import Professional, Specialization
from core.models import Service, TimeStampedModel
from medications.models import MedicationItem  # or your concrete medication model
from events.models import ScheduledDueWindowEvent, ScheduledTimedEvent  # base scheduled event in your project


# =========================
# Templates
# =========================
class CarePlanTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    summary = models.TextField(blank=True, default="")
    version = models.CharField(max_length=32, default="1.0.0")
    is_published = models.BooleanField(default=False)

    applicability_json = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        Professional, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_careplan_templates"
    )

    class Meta:
        unique_together = ("name", "version")
        indexes = [
            models.Index(fields=["name", "version"]),
            models.Index(fields=["is_published"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class GoalTemplate(models.Model):
    template = models.ForeignKey(
        CarePlanTemplate, on_delete=models.CASCADE, related_name="goal_templates"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    target_metric_code = models.CharField(max_length=64, blank=True, default="")
    target_value = models.JSONField(default=dict, blank=True)  # flexible structure
    timeframe_days = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"[GoalTemplate] {self.title}"


class ActionTemplateCategory(models.TextChoices):
    MEDICATION = "MEDICATION", _("Medication")
    APPOINTMENT = "APPOINTMENT", _("Appointment")
    EDUCATION = "EDUCATION", _("Education")
    MEASUREMENT = "MEASUREMENT", _("Measurement")
    TASK = "TASK", _("Task")


class ActionTemplate(models.Model):
    template = models.ForeignKey(
        CarePlanTemplate, on_delete=models.CASCADE, related_name="activity_templates"
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=ActionTemplateCategory.choices)
    instructions_richtext = models.TextField(blank=True, default="")

    required_role = models.CharField(max_length=64, blank=True, default="")
    schedule_json = models.JSONField(default=dict, blank=True)  # e.g. RRULE-like, offsets, windows
    completion_criteria_json = models.JSONField(default=dict, blank=True)

    code = models.CharField(max_length=64, blank=True, default="")
    order_index = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"[ActionTemplate] {self.title} ({self.category})"


# =========================
# Care Plan instances
# =========================
class CarePlanStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    ACTIVE = "ACTIVE", _("Active")
    ON_HOLD = "ON_HOLD", _("On hold")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class CarePlan(TimeStampedModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="careplans")
    template = models.ForeignKey(
        CarePlanTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="instances"
    )
    status = models.CharField(max_length=20, choices=CarePlanStatus.choices, default=CarePlanStatus.PLANNED)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    owner = models.ForeignKey(
        Professional, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_careplans"
    )

    reason_codes = models.JSONField(default=list, blank=True)  # e.g. SNOMED/ICD lists
    notes = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"CarePlan #{self.pk} for {self.patient_id} ({self.status})"


class CarePlanGoalStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    ACHIEVED = "ACHIEVED", _("Achieved")
    CANCELLED = "CANCELLED", _("Cancelled")


class CarePlanGoal(TimeStampedModel):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="goals")
    template = models.ForeignKey(GoalTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="instances")

    title = models.CharField(max_length=255)
    target_metric_code = models.CharField(max_length=64, blank=True, default="")
    target_value_json = models.JSONField(default=dict, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CarePlanGoalStatus.choices, default=CarePlanGoalStatus.PLANNED)

    def __str__(self) -> str:
        return f"Goal #{self.pk} ({self.status})"


# =========================
# Actions + per-category details
# =========================
class ActionCategory(models.TextChoices):
    MEDICATION = "MEDICATION", _("Medication")
    APPOINTMENT = "APPOINTMENT", _("Appointment")
    EDUCATION = "EDUCATION", _("Education")
    MEASUREMENT = "MEASUREMENT", _("Measurement")
    TASK = "TASK", _("Task")


class ActionStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class CarePlanAction(TimeStampedModel):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="actions")
    template = models.ForeignKey(
        ActionTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="instances"
    )

    category = models.CharField(max_length=32, choices=ActionCategory.choices)
    title = models.CharField(max_length=255)

    status = models.CharField(max_length=20, choices=ActionStatus.choices, default=ActionStatus.PLANNED)
    cancel_reason = models.CharField(max_length=128, blank=True, default="")

    completed_at = models.DateTimeField(null=True, blank=True)
    custom_instructions_richtext = models.TextField(blank=True, default="")

    assigned_to = models.ForeignKey(
        Professional, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_careplan_actions"
    )

    schedule_json = models.JSONField(default=dict, blank=True)

    # A small flexible field for category-specific extras that don't justify a dedicated table yet
    extras = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["careplan", "category", "status"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_category_display()}: {self.title}"

    # Soft guard to keep timestamps sane
    def clean(self):
        super().clean()
        if self.status == ActionStatus.COMPLETED and not self.completed_at:
            self.completed_at = self.completed_at or timezone.now()


class MedicationActionDetail(models.Model):
    """Detail for MEDICATION actions — holds actual FK to a MedicationItem and dose info."""
    action = models.OneToOneField(
        CarePlanAction, on_delete=models.CASCADE, related_name="medication_detail"
    )
    medication_item = models.ForeignKey(MedicationItem, on_delete=models.PROTECT)
    dose = models.CharField(max_length=128, blank=True, default="")      # e.g., "500 mg"
    route = models.CharField(max_length=64, blank=True, default="")      # e.g., "oral"
    frequency = models.CharField(max_length=64, blank=True, default="")  # e.g., "BID"
    duration_days = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Medication for action {self.action_id}"

    def clean(self):
        super().clean()
        if self.action.category != ActionCategory.MEDICATION:
            raise ValidationError("MedicationActionDetail must be attached to an action with category MEDICATION.")


class AppointmentActionDetail(models.Model):
    """Detail for APPOINTMENT actions — ties into Service/Specialization and preferred window."""
    action = models.OneToOneField(
        CarePlanAction, on_delete=models.CASCADE, related_name="appointment_detail"
    )
    service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.PROTECT)
    specialization = models.ForeignKey(Specialization, null=True, blank=True, on_delete=models.PROTECT)

    preferred_window_start = models.DateTimeField(null=True, blank=True)
    preferred_window_end = models.DateTimeField(null=True, blank=True)
    location_text = models.CharField(max_length=255, blank=True, default="")
    is_virtual = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"Appointment for action {self.action_id}"

    def clean(self):
        super().clean()
        if self.action.category != ActionCategory.APPOINTMENT:
            raise ValidationError("AppointmentActionDetail must be attached to an action with category APPOINTMENT.")


# =========================
# Scheduled occurrences (ties actions into your scheduling system)
# =========================
class CarePlanActivityEvent(ScheduledDueWindowEvent):
    """
    A concrete scheduled occurrence derived from an action (e.g., a specific dose time,
    a booked appointment slot, a measurement reminder, etc.).
    """
    action = models.ForeignKey(
        CarePlanAction, on_delete=models.CASCADE, related_name="scheduled_events"
    )

    def __str__(self) -> str:
        # ScheduledTimedEvent likely has start/end; adjust as per your base model
        return f"Event for action {self.action_id} ({getattr(self, 'start', None)})"


# =========================
# Reviews
# =========================
class ReviewOutcome(models.TextChoices):
    CONTINUE = "CONTINUE", _("Continue")
    ADJUST = "ADJUST", _("Adjust")
    STOP = "STOP", _("Stop")


class CarePlanReview(models.Model):
    careplan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name="reviews")
    reviewed_by = models.ForeignKey(
        Professional, null=True, blank=True, on_delete=models.SET_NULL, related_name="careplan_reviews"
    )
    review_date = models.DateTimeField(default=timezone.now)
    summary = models.TextField(blank=True, default="")
    outcome = models.CharField(max_length=16, choices=ReviewOutcome.choices, default=ReviewOutcome.CONTINUE)

    # Optional diff / patch capturing changes (e.g., actions/goal updates made during review)
    changes_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-review_date"]

    def __str__(self) -> str:
        return f"Review {self.pk} on CarePlan {self.careplan_id} ({self.outcome})"
