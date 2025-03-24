from django.contrib import admin
from professionals.models import Professional, Role, Specialization
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
            'fields': ('first_name', 'last_name', 'email', 'birth_date', 'role', 'password')
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
