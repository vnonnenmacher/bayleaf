# medications/admin.py
from django.contrib import admin
from django.utils import timezone

from .models import (
    Medication,
    MedicationPrescription,
    MedicationItem,
    TakeMedicationEvent,
)
from events.models import BaseEvent
from medications.helpers.add_medication_helper import AddMedicationHelper


class TakeMedicationEventInline(admin.TabularInline):
    """
    Read-only list of events for the MedicationItem detail page.
    We do not allow adding or editing here to keep the source of truth
    in the helper flows.
    """
    model = TakeMedicationEvent
    fk_name = "medication_item"
    extra = 0
    can_delete = False
    show_change_link = False  # no standalone admin page for this model
    fields = (
        "status",
        "scheduled_to_complete_from",
        "scheduled_to_complete_until",
        "description",
        "created_by",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        # Inline rows are read-only
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Keep deterministic ordering: nearest first
        return qs.order_by("scheduled_to_complete_from")


@admin.action(description="Regenerate pending events (anchor = now)")
def action_regenerate_pending(modeladmin, request, queryset):
    """
    Admin action to rebuild non-completed events for selected items.
    Uses now as the new first-dose anchor.
    """
    helper = AddMedicationHelper(created_by_user=request.user)
    count = 0
    for item in queryset:
        helper.update_item_and_events(
            item=item,
            schedule_changed=True,
            first_dose_at=timezone.now(),
        )
        count += 1
    modeladmin.message_user(request, f"Regenerated pending events for {count} item(s).")


@admin.action(description="Delete pending events (keep completed)")
def action_delete_pending(modeladmin, request, queryset):
    """
    Removes only non-completed events; keeps completed ones for audit/history.
    """
    deleted_total = 0
    for item in queryset:
        deleted_total += item.medication_events.exclude(
            status=BaseEvent.Status.COMPLETED
        ).delete()[0]
    modeladmin.message_user(request, f"Deleted {deleted_total} pending event(s).")


@admin.register(MedicationItem)
class MedicationItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "medication",
        "dosage_amount",
        "dosage_unit",
        "frequency_hours",
        "total_unit_amount",
    )
    list_select_related = ("patient", "medication", "dosage_unit")
    search_fields = (
        "id",
        "instructions",
        "medication__name",
        # add more if you have these fields:
        # "patient__first_name", "patient__last_name",
    )
    list_filter = ("frequency_hours", "dosage_unit", "medication")
    inlines = [TakeMedicationEventInline]
    actions = [action_regenerate_pending, action_delete_pending]


# Keep these registered as usual
@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name")


@admin.register(MedicationPrescription)
class MedicationPrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "created_at")
    list_select_related = ("patient",)
    search_fields = ("id", "patient__id")

# IMPORTANT: do NOT register TakeMedicationEvent here
# admin.site.register(TakeMedicationEvent)  # ← remove/keep commented out
