from django.conf import settings
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from documents.serializers import DocumentSerializer
from documents.storage import get_documents_storage_client
from professionals.models import Professional
from professionals.permissions import IsProfessional


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


def _parse_minio_reference(reference):
    if not reference or not reference.startswith("minio://"):
        return None, None

    payload = reference[len("minio://") :]
    parts = payload.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None, None
    return parts[0], parts[1]


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsProfessional]

    def get_queryset(self):
        organization = _get_professional_org_or_403(self.request)
        queryset = Document.objects.filter(org_id=organization.id).order_by("name", "doc_key")

        doc_key = self.request.query_params.get("doc_key")
        if doc_key:
            queryset = queryset.filter(doc_key=doc_key)

        search_doc_key = self.request.query_params.get("search_doc_key")
        if search_doc_key:
            queryset = queryset.filter(doc_key__startswith=search_doc_key)

        search_name = self.request.query_params.get("search_name")
        if search_name:
            queryset = queryset.filter(name__icontains=search_name)

        mime_type = self.request.query_params.get("mime_type")
        if mime_type:
            queryset = queryset.filter(mime_type=mime_type)

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


class DocumentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsProfessional]

    def get_queryset(self):
        organization = _get_professional_org_or_403(self.request)
        return Document.objects.filter(org_id=organization.id)


class DocumentDownloadURLView(APIView):
    permission_classes = [IsProfessional]

    def get(self, request, pk):
        organization = _get_professional_org_or_403(request)
        document = generics.get_object_or_404(Document, id=pk, org_id=organization.id)

        bucket, object_key = _parse_minio_reference(document.reference)
        if bucket and object_key:
            storage = get_documents_storage_client()
            url = storage.presign_get(bucket, object_key)
            return Response(
                {"url": url, "expires_in": settings.MINIO_PRESIGN_EXPIRES},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"url": document.reference, "expires_in": None},
            status=status.HTTP_200_OK,
        )
