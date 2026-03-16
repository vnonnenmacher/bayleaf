from django.db.models import OuterRef, Q, Subquery
from django.conf import settings
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import DocumentFamily, DocumentVersion
from documents.serializers import (
    DocumentFamilySerializer,
    DocumentVersionSerializer,
    DocumentVersionUploadSerializer,
)
from documents.services import delete_document_family, publish_version
from documents.storage import get_documents_storage_client
from professionals.models import Professional
from professionals.permissions import IsProfessional


def _document_family_queryset_with_latest_version():
    latest_version_uuid_subquery = (
        DocumentVersion.objects.filter(family_id=OuterRef("pk")).order_by("-created_at").values("id")[:1]
    )
    return DocumentFamily.objects.annotate(latest_version_uuid=Subquery(latest_version_uuid_subquery))


def _get_professional_org_or_403(request):
    professional = (
        Professional.objects.filter(user_ptr_id=request.user.id)
        .prefetch_related("organizations")
        .first()
    )
    if not professional:
        raise PermissionDenied("Authenticated user is not a professional.")

    organization = professional.organizations.order_by("name", "id").first()
    if not organization:
        raise PermissionDenied("Professional must belong to an organization.")

    return organization


class DocumentFamilyListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentFamilySerializer
    permission_classes = [IsProfessional]

    def get_queryset(self):
        organization = _get_professional_org_or_403(self.request)
        queryset = _document_family_queryset_with_latest_version().order_by("title", "doc_key")
        queryset = queryset.filter(org_id=organization.id)

        doc_key = self.request.query_params.get("doc_key")
        if doc_key:
            queryset = queryset.filter(doc_key=doc_key)

        search_doc_key = self.request.query_params.get("search_doc_key")
        if search_doc_key:
            queryset = queryset.filter(doc_key__startswith=search_doc_key)

        doc_type = self.request.query_params.get("doc_type")
        if doc_type:
            queryset = queryset.filter(doc_type=doc_type)

        tags = self.request.query_params.getlist("tags")
        if not tags:
            single_tag = self.request.query_params.get("tags")
            if single_tag:
                tags = [single_tag]
        if tags:
            tag_query = Q()
            for tag in tags:
                tag_query &= Q(tags__contains=[tag])
            queryset = queryset.filter(tag_query)

        return queryset

    def perform_create(self, serializer):
        organization = _get_professional_org_or_403(self.request)
        serializer.save(org=organization)


class DocumentFamilyRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentFamilySerializer
    permission_classes = [IsProfessional]

    def get_queryset(self):
        organization = _get_professional_org_or_403(self.request)
        return _document_family_queryset_with_latest_version().filter(org_id=organization.id)

    def destroy(self, request, *args, **kwargs):
        family = self.get_object()
        try:
            delete_document_family(family.id)
        except DocumentFamily.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentVersionListView(generics.ListAPIView):
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsProfessional]

    def get_queryset(self):
        organization = _get_professional_org_or_403(self.request)
        return DocumentVersion.objects.filter(
            family_id=self.kwargs["family_id"],
            family__org_id=organization.id,
        ).order_by("-created_at")


class DocumentVersionRetrieveView(generics.RetrieveAPIView):
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsProfessional]

    def get_queryset(self):
        organization = _get_professional_org_or_403(self.request)
        return DocumentVersion.objects.select_related("family", "created_by").filter(
            family__org_id=organization.id
        )


class DocumentVersionUploadView(generics.CreateAPIView):
    serializer_class = DocumentVersionUploadSerializer
    permission_classes = [IsProfessional]

    def create(self, request, *args, **kwargs):
        organization = _get_professional_org_or_403(request)
        family = generics.get_object_or_404(DocumentFamily, id=self.kwargs["family_id"], org_id=organization.id)
        serializer = self.get_serializer(data=request.data, context={"request": request, "family": family})
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        output = DocumentVersionSerializer(version, context={"request": request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class DocumentVersionPublishView(APIView):
    permission_classes = [IsProfessional]

    def post(self, request, pk):
        organization = _get_professional_org_or_403(request)
        effective_from_raw = request.data.get("effective_from")
        effective_from = None
        if effective_from_raw:
            effective_from = parse_date(effective_from_raw)
            if effective_from is None:
                return Response(
                    {"detail": "Invalid effective_from format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            version = DocumentVersion.objects.get(id=pk, family__org_id=organization.id)
            version = publish_version(version.id, effective_from=effective_from)
        except DocumentVersion.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(DocumentVersionSerializer(version).data, status=status.HTTP_200_OK)


class DocumentVersionDownloadURLView(APIView):
    permission_classes = [IsProfessional]

    def get(self, request, pk):
        organization = _get_professional_org_or_403(request)
        version = generics.get_object_or_404(DocumentVersion, id=pk, family__org_id=organization.id)
        storage = get_documents_storage_client()
        url = storage.presign_get(version.bucket, version.object_key)
        return Response(
            {"url": url, "expires_in": settings.MINIO_PRESIGN_EXPIRES},
            status=status.HTTP_200_OK,
        )
