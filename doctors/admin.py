from django.contrib import admin
from .models import Shift, Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("did", "email")
    search_fields = ("email",)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("doctor", "weekday", "service", "from_time", "to_time", "slot_duration")
    list_filter = ("weekday", "doctor", "service")
    search_fields = ("doctor__email", "service__name")
    ordering = ("doctor", "weekday", "from_time")
