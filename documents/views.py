from django.db.models import Q
from django.conf import settings
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import DocumentFamily, DocumentVersion
from documents.serializers import (
    DocumentFamilySerializer,
    DocumentVersionSerializer,
    DocumentVersionUploadSerializer,
)
from documents.services import publish_version
from documents.storage import get_documents_storage_client
from professionals.permissions import IsAgentOrProfessional


class DocumentFamilyListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentFamilySerializer
    permission_classes = [IsAgentOrProfessional]

    def get_queryset(self):
        queryset = DocumentFamily.objects.all().order_by("title", "doc_key")

        org = self.request.query_params.get("org")
        if org:
            queryset = queryset.filter(org_id=org)

        doc_key = self.request.query_params.get("doc_key")
        if doc_key:
            queryset = queryset.filter(doc_key=doc_key)

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


class DocumentFamilyRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = DocumentFamily.objects.all()
    serializer_class = DocumentFamilySerializer
    permission_classes = [IsAgentOrProfessional]


class DocumentVersionListView(generics.ListAPIView):
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsAgentOrProfessional]

    def get_queryset(self):
        return DocumentVersion.objects.filter(family_id=self.kwargs["family_id"]).order_by("-created_at")


class DocumentVersionRetrieveView(generics.RetrieveAPIView):
    queryset = DocumentVersion.objects.select_related("family", "created_by").all()
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsAgentOrProfessional]


class DocumentVersionUploadView(generics.CreateAPIView):
    serializer_class = DocumentVersionUploadSerializer
    permission_classes = [IsAgentOrProfessional]

    def create(self, request, *args, **kwargs):
        family = generics.get_object_or_404(DocumentFamily, id=self.kwargs["family_id"])
        serializer = self.get_serializer(data=request.data, context={"request": request, "family": family})
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        output = DocumentVersionSerializer(version, context={"request": request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class DocumentVersionPublishView(APIView):
    permission_classes = [IsAgentOrProfessional]

    def post(self, request, pk):
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
            version = publish_version(pk, effective_from=effective_from)
        except DocumentVersion.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(DocumentVersionSerializer(version).data, status=status.HTTP_200_OK)


class DocumentVersionDownloadURLView(APIView):
    permission_classes = [IsAgentOrProfessional]

    def get(self, request, pk):
        version = generics.get_object_or_404(DocumentVersion, id=pk)
        storage = get_documents_storage_client()
        url = storage.presign_get(version.bucket, version.object_key)
        return Response(
            {"url": url, "expires_in": settings.MINIO_PRESIGN_EXPIRES},
            status=status.HTTP_200_OK,
        )
