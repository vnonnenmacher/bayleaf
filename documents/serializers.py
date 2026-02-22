import os
from uuid import uuid4

from django.conf import settings
from rest_framework import serializers

from documents.models import DocumentFamily, DocumentVersion
from documents.storage import get_documents_storage_client
from professionals.models import Professional


class DocumentFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentFamily
        fields = [
            "id",
            "org",
            "doc_key",
            "title",
            "doc_type",
            "description",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "org": {"required": False, "allow_null": True},
        }


class DocumentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "family",
            "version_label",
            "status",
            "effective_from",
            "effective_to",
            "storage_provider",
            "bucket",
            "object_key",
            "content_type",
            "size_bytes",
            "content_hash",
            "index_status",
            "indexed_at",
            "index_error",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "family",
            "size_bytes",
            "content_hash",
            "indexed_at",
            "index_error",
            "created_by",
            "created_at",
        ]

    def validate(self, attrs):
        if self.instance is None:
            request = self.context.get("request")
            has_uploaded_file = bool(request and getattr(request, "FILES", None) and request.FILES.get("file"))
            if not has_uploaded_file:
                bucket = attrs.get("bucket")
                object_key = attrs.get("object_key")
                if not bucket or not object_key:
                    raise serializers.ValidationError("'bucket' and 'object_key' are required when creating a version.")
        return attrs


class DocumentVersionUploadSerializer(serializers.Serializer):
    version_label = serializers.CharField(max_length=64)
    status = serializers.ChoiceField(
        choices=DocumentVersion.Status.choices,
        required=False,
        default=DocumentVersion.Status.DRAFT,
    )
    file = serializers.FileField()

    def validate_file(self, value):
        allowed_content_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        }
        if value.content_type and value.content_type not in allowed_content_types:
            raise serializers.ValidationError("Only PDF and Word documents (DOC/DOCX) are supported.")
        return value

    def create(self, validated_data):
        family = self.context["family"]
        request = self.context.get("request")
        professional = None
        if request and request.user and request.user.is_authenticated:
            professional = Professional.objects.filter(user_ptr_id=request.user.id).first()

        upload = validated_data["file"]
        version = DocumentVersion(
            id=uuid4(),
            family=family,
            version_label=validated_data["version_label"],
            status=validated_data.get("status", DocumentVersion.Status.DRAFT),
            storage_provider=DocumentVersion.StorageProvider.MINIO,
            bucket=settings.BAYLEAF_DOCS_BUCKET,
            object_key="",
            content_type=upload.content_type or "application/octet-stream",
            created_by=professional,
        )

        original_filename = os.path.basename(upload.name)
        org_segment = str(family.org_id) if family.org_id else "unscoped"
        version.object_key = f"org/{org_segment}/documents/{family.id}/{version.id}/{original_filename}"

        storage = get_documents_storage_client()
        size_bytes, sha256 = storage.upload_fileobj(
            upload.file,
            version.bucket,
            version.object_key,
            version.content_type,
        )

        version.size_bytes = size_bytes
        version.content_hash = sha256
        version.save()
        return version
