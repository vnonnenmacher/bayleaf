import uuid

from django.db import models


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    doc_key = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=1024)
    mime_type = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(
        "professionals.Professional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["org", "doc_key"], name="uniq_document_org_doc_key"),
        ]
        ordering = ["name", "doc_key"]

    def __str__(self):
        return f"{self.doc_key} ({self.name})"
