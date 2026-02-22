import uuid

from django.db import models
from django.db.models import Q


class DocumentFamily(models.Model):
    class DocumentType(models.TextChoices):
        SOP = "SOP", "SOP"
        MANUAL = "MANUAL", "Manual"
        POLICY = "POLICY", "Policy"
        FORM = "FORM", "Form"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="document_families",
        null=True,
        blank=True,
    )
    doc_key = models.CharField(max_length=128)
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=16, choices=DocumentType.choices)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["org", "doc_key"], name="uniq_document_family_org_doc_key"),
        ]
        ordering = ["title", "doc_key"]

    def __str__(self):
        return f"{self.doc_key} ({self.title})"


class DocumentVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        EFFECTIVE = "EFFECTIVE", "Effective"
        SUPERSEDED = "SUPERSEDED", "Superseded"
        ARCHIVED = "ARCHIVED", "Archived"

    class StorageProvider(models.TextChoices):
        MINIO = "minio", "MinIO"
        S3 = "s3", "S3"

    class IndexStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        INDEXED = "INDEXED", "Indexed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(DocumentFamily, on_delete=models.CASCADE, related_name="versions")
    version_label = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    storage_provider = models.CharField(
        max_length=16,
        choices=StorageProvider.choices,
        default=StorageProvider.MINIO,
    )
    bucket = models.CharField(max_length=128)
    object_key = models.CharField(max_length=512)
    content_type = models.CharField(max_length=128, blank=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)

    index_status = models.CharField(
        max_length=16,
        choices=IndexStatus.choices,
        default=IndexStatus.PENDING,
    )
    indexed_at = models.DateTimeField(null=True, blank=True)
    index_error = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "professionals.Professional",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["family", "version_label"], name="uniq_document_version_family_label"),
            models.UniqueConstraint(
                fields=["family"],
                condition=Q(status="EFFECTIVE"),
                name="uniq_effective_document_version_per_family",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.family.doc_key} - {self.version_label}"
