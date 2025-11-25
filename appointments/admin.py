# appointments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Appointment  # :contentReference[oaicite:1]{index=1}
from events.models import EventStatusHistory  # :contentReference[oaicite:2]{index=2}


class EventStatusHistoryInline(admin.TabularInline):
    """
    Read-only audit log showing each status change.
    """
    model = EventStatusHistory
    extra = 0
    can_delete = False
    fields = ("previous_status", "new_status", "changed_by", "changed_at")
    readonly_fields = fields
    ordering = ("-changed_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Beautiful, useful admin for managing appointments.
    """

    list_display = (
        "id",
        "professional_display",
        "patient_display",
        "service",
        "slot_display",
        "scheduled_to",
        "duration_minutes",
        "status_colored",
        "created_at",
    )

    list_filter = (
        "status",
        "service",
        "professional",
        "patient",
        ("scheduled_to", admin.DateFieldListFilter),
        ("service_slot", admin.EmptyFieldListFilter),
    )

    search_fields = (
        "professional__first_name", "professional__last_name", "professional__email",
        "patient__first_name", "patient__last_name", "patient__email",
        "service__name",
    )

    ordering = ("-scheduled_to",)
    readonly_fields = ("event_type", "created_at", "created_by", "status")
    inlines = [EventStatusHistoryInline]

    fieldsets = (
        ("Appointment Info", {
            "fields": (
                "professional",
                "patient",
                "service",
                "service_slot",
                "scheduled_to",
                "duration_minutes",
            )
        }),
        ("Event Status", {
            "fields": (
                "status",
                "event_type",
            )
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at")
        })
    )

    # ----------------------------------
    # DISPLAY HELPERS
    # ----------------------------------

    def professional_display(self, obj):
        return f"{obj.professional.full_name} ({obj.professional.email})"
    professional_display.short_description = "Professional"

    def patient_display(self, obj):
        return f"{obj.patient.first_name} ({obj.patient.email})"
    patient_display.short_description = "Patient"

    def slot_display(self, obj):
        if not obj.service_slot:
            return "—"
        return f"{obj.service_slot.start_time:%H:%M}–{obj.service_slot.end_time:%H:%M}"
    slot_display.short_description = "Slot"

    def status_colored(self, obj):
        color_map = {
            "REQUESTED": "#999",
            "CONFIRMED": "#2563eb",
            "INITIATED": "#7c3aed",
            "COMPLETED": "#16a34a",
            "CANCELED": "#dc2626",
            "RESCHEDULED": "#d97706",
        }
        color = color_map.get(obj.status, "#555")
        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = "Status"

    # ----------------------------------
    # AUTO-FILL created_by
    # ----------------------------------

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
