from django.contrib import admin

from documents.models import DocumentFamily, DocumentVersion


@admin.register(DocumentFamily)
class DocumentFamilyAdmin(admin.ModelAdmin):
    list_display = ("doc_key", "title", "doc_type", "org", "created_at", "updated_at")
    list_filter = ("doc_type", "org")
    search_fields = ("doc_key", "title", "description")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = (
        "family",
        "version_label",
        "status",
        "index_status",
        "effective_from",
        "effective_to",
        "bucket",
        "created_at",
    )
    list_filter = ("status", "index_status", "storage_provider", "bucket")
    search_fields = ("family__doc_key", "family__title", "version_label", "object_key", "content_hash")
    autocomplete_fields = ("family", "created_by")
