from django.contrib import admin
from .models import Shift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("doctor", "weekday", "service")
    list_filter = ("weekday", "doctor", "service")
    search_fields = ("doctor__email", "service__name")
