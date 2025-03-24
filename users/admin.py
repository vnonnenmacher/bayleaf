from django.contrib import admin

from users.models import Identifier, IdentifierType


@admin.register(IdentifierType)
class IdentifierTypeAdmin(admin.ModelAdmin):
    search_fields = ['name']  # ✅ Required for autocomplete_fields to work


# Register your models here.
class IdentifierInline(admin.TabularInline):
    model = Identifier
    extra = 0
    autocomplete_fields = ['type']
