import uuid

from django.db import models


class Document(models.Model):
    class Source(models.TextChoices):
        MINIO = "minio", "MinIO"
        AD = "ad", "Active Directory"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    # dot-separated grouping path, e.g. "radiology.2024"; null means root
    path = models.CharField(max_length=1024, blank=True, null=True)
    doc_key = models.CharField(max_length=128, blank=True)
    name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=512, blank=True)
    reference = models.CharField(max_length=1024, blank=True)
    mime_type = models.CharField(max_length=128, blank=True)
    source = models.CharField(max_length=32, choices=Source.choices, default=Source.MINIO)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    md5sum = models.CharField(max_length=32, blank=True)
    version = models.CharField(max_length=64, blank=True, null=True)
    parent_document = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="versions",
    )
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
