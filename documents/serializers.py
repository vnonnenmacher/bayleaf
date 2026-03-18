import os
import re
from uuid import uuid4

from django.conf import settings
from rest_framework import serializers

from documents.models import Document
from documents.storage import get_documents_storage_client
from professionals.models import Professional


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)
    name = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)
    mime_type = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "org",
            "doc_key",
            "name",
            "reference",
            "mime_type",
            "description",
            "tags",
            "size_bytes",
            "content_hash",
            "created_by",
            "created_at",
            "updated_at",
            "file",
        ]
        read_only_fields = [
            "id",
            "org",
            "size_bytes",
            "content_hash",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        file_obj = attrs.get("file")
        reference = attrs.get("reference")
        mime_type = attrs.get("mime_type")
        name = attrs.get("name")

        if self.instance is None:
            if not file_obj and not reference:
                raise serializers.ValidationError(
                    {"reference": "Either 'reference' or 'file' must be provided."}
                )
            if not mime_type and not file_obj:
                raise serializers.ValidationError(
                    {"mime_type": "This field is required when no file is uploaded."}
                )

        if not name:
            if file_obj:
                attrs["name"] = self._name_from_filename(file_obj.name)
            elif reference:
                attrs["name"] = self._name_from_reference(reference)

        if file_obj:
            inferred_mime_type = file_obj.content_type or "application/octet-stream"
            attrs["mime_type"] = mime_type or inferred_mime_type

        return attrs

    def create(self, validated_data):
        upload = validated_data.pop("file", None)
        request = self.context.get("request")
        professional = None
        if request and request.user and request.user.is_authenticated:
            professional = Professional.objects.filter(user_ptr_id=request.user.id).first()

        if professional:
            validated_data["created_by"] = professional

        document = Document(**validated_data)
        if upload:
            self._upload_file_to_storage(document=document, upload=upload)
        document.save()
        return document

    def update(self, instance, validated_data):
        upload = validated_data.pop("file", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if upload:
            self._upload_file_to_storage(document=instance, upload=upload)

        instance.save()
        return instance

    def _upload_file_to_storage(self, document, upload):
        org = document.org
        if org is None and document.pk:
            org = Document.objects.only("org_id").get(pk=document.pk).org

        org_segment = str(org.id) if org else "unscoped"
        original_filename = os.path.basename(upload.name)
        safe_filename = self._safe_storage_filename(original_filename)
        object_key = f"org/{org_segment}/documents/{document.id}/{uuid4()}/{safe_filename}"
        bucket = settings.BAYLEAF_DOCS_BUCKET
        content_type = document.mime_type or upload.content_type or "application/octet-stream"

        storage = get_documents_storage_client()
        size_bytes, sha256 = storage.upload_fileobj(upload.file, bucket, object_key, content_type)

        document.reference = f"minio://{bucket}/{object_key}"
        document.mime_type = content_type
        document.size_bytes = size_bytes
        document.content_hash = sha256

    def _name_from_filename(self, filename):
        base_name = os.path.basename(filename)
        stem, _ext = os.path.splitext(base_name)
        return stem or base_name or "document"

    def _name_from_reference(self, reference):
        base_name = reference.rstrip("/").split("/")[-1]
        stem, _ext = os.path.splitext(base_name)
        return stem or base_name or "document"

    def _safe_storage_filename(self, filename):
        stem, ext = os.path.splitext(filename)
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
        if not normalized:
            normalized = "document"
        clean_ext = re.sub(r"[^A-Za-z0-9.]+", "", ext)
        return f"{normalized}{clean_ext}"
