from django.contrib import admin

from documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "doc_key",
        "name",
        "mime_type",
        "org",
        "reference",
        "size_bytes",
        "created_at",
        "updated_at",
    )
    list_filter = ("mime_type", "org")
    search_fields = ("doc_key", "name", "reference", "description", "content_hash")
    autocomplete_fields = ("created_by",)
