from django.contrib import admin
from professionals.models import Professional, Role, Shift, Specialization
from users.admin import IdentifierInline  # if in a separate file


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'role']
    list_filter = ['role']
    search_fields = ['first_name', 'last_name', 'email']
    inlines = [IdentifierInline]
    autocomplete_fields = ['role', 'address1', 'address2', 'primary_contact', 'secondary_contact']
    filter_horizontal = ['services', 'specializations']  # ✅ These now work

    fieldsets = (
        ("Basic Info", {
            'fields': ('first_name', 'last_name', 'email', 'birth_date', 'role', 'password', 'bio')
        }),
        ("Address", {
            'fields': ('address1', 'address2'),
            'classes': ('collapse',),
        }),
        ("Contact Info", {
            'fields': ('primary_contact', 'secondary_contact'),
            'classes': ('collapse',),
        }),
        ("Professional Tags", {
            'fields': ('services', 'specializations'),
        }),
    )


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ["professional", "service", "weekday", "from_time", "to_time", "slot_duration"]
    list_filter = ["weekday", "service", "professional"]
    search_fields = ["professional__first_name", "professional__last_name", "professional__email"]
    autocomplete_fields = ["professional", "service"]
    ordering = ["professional", "weekday", "from_time"]
