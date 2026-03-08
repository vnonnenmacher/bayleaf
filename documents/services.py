from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from documents.models import DocumentFamily, DocumentVersion
from documents.storage import get_documents_storage_client


@transaction.atomic
def publish_version(version_id, effective_from=None):
    target = (
        DocumentVersion.objects.select_for_update()
        .select_related("family")
        .get(id=version_id)
    )

    publish_date = effective_from or timezone.localdate()

    currently_effective = (
        DocumentVersion.objects.select_for_update()
        .filter(family=target.family, status=DocumentVersion.Status.EFFECTIVE)
        .exclude(id=target.id)
        .first()
    )

    if currently_effective:
        currently_effective.status = DocumentVersion.Status.SUPERSEDED
        currently_effective.effective_to = publish_date - timedelta(days=1)
        currently_effective.save(update_fields=["status", "effective_to"])

    target.status = DocumentVersion.Status.EFFECTIVE
    target.effective_from = publish_date
    target.effective_to = None
    target.save(update_fields=["status", "effective_from", "effective_to"])

    return target


@transaction.atomic
def delete_document_family(family_id):
    family = DocumentFamily.objects.select_for_update().get(id=family_id)
    versions = list(
        DocumentVersion.objects.select_for_update()
        .filter(family=family)
        .only("bucket", "object_key")
    )

    if versions:
        storage = get_documents_storage_client()
        for version in versions:
            storage.delete_object(version.bucket, version.object_key)

    family.delete()
