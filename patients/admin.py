from django.contrib import admin
from patients.models import Patient
from users.admin import IdentifierInline


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'birth_date']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [IdentifierInline]
    autocomplete_fields = ['address1', 'address2', 'primary_contact', 'secondary_contact']

    fieldsets = (
        ("Basic Info", {
            'fields': ('first_name', 'last_name', 'email', 'birth_date', 'password')
        }),
        ("Address & Contact", {
            'fields': ('address1', 'address2', 'primary_contact', 'secondary_contact'),
            'classes': ('collapse',),
        }),
        # ❌ Don't include `groups`, `user_permissions`, `is_staff`, etc.
    )
