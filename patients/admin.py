# patients/admin.py
from django.contrib import admin
from django.utils import timezone

from patients.models import Patient
from users.admin import IdentifierInline

# import medication + events models
from medications.models import MedicationItem, TakeMedicationEvent
from events.models import BaseEvent


class MedicationItemInline(admin.TabularInline):
    """
    Inline section on the Patient page showing the medications this patient is taking.
    Includes quick, read-only insights about the dosing/events.
    """
    model = MedicationItem
    fk_name = "patient"
    extra = 0
    show_change_link = True  # allow jumping to the MedicationItem admin page
    # What we display in the table
    fields = (
        "medication",
        "dosage_amount",
        "dosage_unit",
        "frequency_hours",
        "total_unit_amount",
        "instructions",
        "next_dose_window",
        "pending_events",
        "completed_events",
    )
    readonly_fields = (
        "next_dose_window",
        "pending_events",
        "completed_events",
    )

    def get_queryset(self, request):
        # Keep deterministic order (newest first or by med name—pick your preference)
        qs = super().get_queryset(request)
        return qs.select_related("medication", "dosage_unit").order_by("-id")

    # ---- Computed read-only columns ----

    def next_dose_window(self, obj: MedicationItem):
        """
        Show the next upcoming window among NOT completed events, earliest first.
        """
        next_evt = (
            obj.medication_events
            .exclude(status=BaseEvent.Status.COMPLETED)
            .order_by("scheduled_to_complete_from")
            .first()
        )
        if not next_evt:
            return "-"
        start = timezone.localtime(next_evt.scheduled_to_complete_from)
        end = timezone.localtime(next_evt.scheduled_to_complete_until)
        return f"{start:%Y-%m-%d %H:%M} → {end:%H:%M}"

    next_dose_window.short_description = "Next dose window"

    def pending_events(self, obj: MedicationItem) -> int:
        """
        Count all events that are not completed (upcoming/overdue).
        """
        return obj.medication_events.exclude(status=BaseEvent.Status.COMPLETED).count()

    pending_events.short_description = "Pending events"

    def completed_events(self, obj: MedicationItem) -> int:
        """
        Count completed events for quick audit visibility.
        """
        return obj.medication_events.filter(status=BaseEvent.Status.COMPLETED).count()

    completed_events.short_description = "Completed events"


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "email", "birth_date"]
    search_fields = ["first_name", "last_name", "email"]
    inlines = [IdentifierInline, MedicationItemInline]
    autocomplete_fields = ["address1", "address2", "primary_contact", "secondary_contact"]

    fieldsets = (
        ("Basic Info", {
            "fields": ("first_name", "last_name", "email", "birth_date", "password")
        }),
        ("Address & Contact", {
            "fields": ("address1", "address2", "primary_contact", "secondary_contact"),
            "classes": ("collapse",),
        }),
        # The Medications section appears automatically via the MedicationItemInline
    )
