from django.contrib import admin
from .models import Address, Contact, DosageUnit, Organization, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "description")
    search_fields = ("name", "code")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("street", "city", "state", "country")
    search_fields = ("city", "state", "country")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "email")
    search_fields = ("phone_number", "email")


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


class ContactInline(admin.StackedInline):
    model = Contact
    extra = 0


admin.site.register(DosageUnit)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
