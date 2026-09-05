from unittest.mock import Mock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from core.models import Organization
from documents.models import Document


def _make_document(org, **overrides):
    defaults = {
        "org": org,
        "path": "radiology.2024",
        "doc_key": "chest-xray",
        "name": "Chest X-Ray",
        "file_name": "chest_xray.dcm",
        "reference": "minio://bayleaf-documents/org/uuid/documents/uuid/uuid/chest_xray.dcm",
        "mime_type": "application/dicom",
        "source": Document.Source.MINIO,
        "description": "Existing document",
        "tags": ["radiology", "xray"],
        "size_bytes": 512000,
        "md5sum": "d41d8cd98f00b204e9800998ecf8427e",
        "version": "v1",
        "parent_document": None,
    }
    defaults.update(overrides)
    return Document.objects.create(**defaults)


@pytest.mark.django_db
@patch("documents.serializers.get_documents_storage_client")
def test_document_create_file_upload_matches_endpoint_contract(mock_storage, api_client, professional):
    mock_client = Mock()
    mock_client.upload_fileobj.return_value = (512000, "d41d8cd98f00b204e9800998ecf8427e")
    mock_client.presign_get.return_value = (
        "https://minio.example.com/bayleaf-documents/org/uuid/documents/uuid/uuid/chest_xray.dcm?X-Amz-Expires=900"
    )
    mock_storage.return_value = mock_client

    api_client.force_authenticate(user=professional)

    file_upload = SimpleUploadedFile(
        "chest_xray.dcm",
        b"\x00\x01\x02\x03",
        content_type="application/dicom",
    )

    response = api_client.post(
        reverse("document-list-create"),
        data={
            "file": file_upload,
            "path": "radiology.2024",
            "description": "Chest X-Ray taken in consultation",
            "tags": '["radiology","xray"]',
            "version": "v1",
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["path"] == "radiology.2024"
    assert response.data["name"] == "chest_xray"
    assert response.data["doc_key"] == "chest_xray"
    assert response.data["file_name"] == "chest_xray.dcm"
    assert response.data["reference"].startswith("minio://")
    assert response.data["mime_type"] == "application/dicom"
    assert response.data["source"] == "minio"
    assert response.data["description"] == "Chest X-Ray taken in consultation"
    assert response.data["tags"] == ["radiology", "xray"]
    assert response.data["size_bytes"] == 512000
    assert response.data["md5sum"] == "d41d8cd98f00b204e9800998ecf8427e"
    assert response.data["version"] == "v1"
    assert response.data["parent_document"] is None
    assert response.data["created_by"] is not None

    document = Document.objects.get(pk=response.data["id"])
    assert document.org_id is not None
    assert document.doc_key == "chest_xray"
    assert document.name == "chest_xray"
    assert document.path == "radiology.2024"
    assert document.description == "Chest X-Ray taken in consultation"
    assert document.tags == ["radiology", "xray"]


@pytest.mark.django_db
@patch("documents.serializers.get_documents_storage_client")
def test_document_create_minimal_file_upload_is_valid(mock_storage, api_client, professional):
    mock_client = Mock()
    mock_client.upload_fileobj.return_value = (512000, "d41d8cd98f00b204e9800998ecf8427e")
    mock_client.presign_get.return_value = (
        "https://minio.example.com/bayleaf-documents/org/uuid/documents/uuid/uuid/report.pdf?X-Amz-Expires=900"
    )
    mock_storage.return_value = mock_client

    api_client.force_authenticate(user=professional)
    file_upload = SimpleUploadedFile(
        "report.pdf",
        b"hello world",
        content_type="application/pdf",
    )

    response = api_client.post(
        reverse("document-list-create"),
        data={"file": file_upload},
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "report"
    assert response.data["doc_key"] == "report"
    assert response.data["file_name"] == "report.pdf"
    assert response.data["mime_type"] == "application/pdf"
    assert response.data["source"] == "minio"


@pytest.mark.django_db
@patch("documents.serializers.get_documents_storage_client")
def test_document_create_external_reference_matches_endpoint_contract(mock_storage, api_client, professional):
    mock_client = Mock()
    mock_client.upload_fileobj.return_value = (0, "d41d8cd98f00b204e9800998ecf8427e")
    mock_client.presign_get.return_value = (
        "https://minio.example.com/bayleaf-documents/org/uuid/documents/uuid/uuid/ecg.pdf?X-Amz-Expires=900"
    )
    mock_storage.return_value = mock_client

    api_client.force_authenticate(user=professional)
    response = api_client.post(
        reverse("document-list-create"),
        data={
            "reference": "https://records.hospital.org/patient/12345/ecg.pdf",
            "mime_type": "application/pdf",
            "name": "ECG Report",
            "source": "other",
            "path": "cardiology.2024",
            "tags": ["ecg", "cardiology"],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["reference"] == "https://records.hospital.org/patient/12345/ecg.pdf"
    assert response.data["mime_type"] == "application/pdf"
    assert response.data["name"] == "ECG Report"
    assert response.data["path"] == "cardiology.2024"
    assert response.data["source"] == "other"
    assert response.data["tags"] == ["ecg", "cardiology"]
    assert response.data["org"] is not None


@pytest.mark.django_db
def test_document_list_returns_only_org_documents_and_filters(api_client, professional):
    api_client.force_authenticate(user=professional)

    organization = Organization.objects.create(name=professional.email, code="doc-org-1")
    other_org = Organization.objects.create(name="Other Org", code="doc-org-2")
    professional.organizations.add(organization)

    _make_document(organization, doc_key="chest-xray", name="Chest X-Ray", tags=["radiology", "xray"])
    _make_document(organization, doc_key="ecg-report", name="ECG Report", tags=["cardiology"])
    _make_document(other_org, doc_key="outside-doc", name="Outside Doc", tags=["radiology"])

    response = api_client.get(reverse("document-list-create"), {"search_name": "chest", "tags": "radiology"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["doc_key"] == "chest-xray"
    assert response.data["results"][0]["name"] == "Chest X-Ray"


@pytest.mark.django_db
def test_document_detail_returns_scoped_document(api_client, professional):
    api_client.force_authenticate(user=professional)
    organization = Organization.objects.create(name=professional.email, code="doc-org-3")
    professional.organizations.add(organization)

    document = _make_document(organization, doc_key="single-doc", name="Single Doc")

    response = api_client.get(reverse("document-retrieve-update-destroy", kwargs={"pk": document.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(document.id)
    assert response.data["name"] == "Single Doc"
    assert response.data["doc_key"] == "single-doc"


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
@patch("documents.serializers.get_documents_storage_client")
def test_document_patch_updates_metadata_and_replaces_file(mock_storage, api_client, professional):
    mock_client = Mock()
    mock_client.upload_fileobj.return_value = (2048, "7d2b8d5a9563a0f0d7e489a0e57d0b8f")
    mock_client.presign_get.return_value = (
        "https://minio.example.com/bayleaf-documents/org/uuid/documents/uuid/uuid/updated.pdf?X-Amz-Expires=900"
    )
    mock_storage.return_value = mock_client

    api_client.force_authenticate(user=professional)
    organization = Organization.objects.create(name=professional.email, code="doc-org-4")
    professional.organizations.add(organization)
    document = _make_document(organization, doc_key="document-v1", name="Existing Doc")

    response = api_client.patch(
        reverse("document-retrieve-update-destroy", kwargs={"pk": document.id}),
        data={
            "name": "Updated doc",
            "description": "Reviewed by Dr. Smith",
            "tags": '["reviewed","radiology"]',
            "file": SimpleUploadedFile("updated.pdf", b"updated bytes", content_type="application/pdf"),
            "version": "v2",
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Updated doc"
    assert response.data["description"] == "Reviewed by Dr. Smith"
    assert response.data["tags"] == ["reviewed", "radiology"]
    assert response.data["version"] == "v2"
    assert response.data["file_name"] == "updated.pdf"
    assert response.data["mime_type"] == "application/pdf"
    assert response.data["reference"].startswith("minio://")


@pytest.mark.django_db
def test_document_delete_removes_record(api_client, professional):
    api_client.force_authenticate(user=professional)
    organization = Organization.objects.create(name=professional.email, code="doc-org-5")
    professional.organizations.add(organization)
    document = _make_document(organization, doc_key="delete-me", name="Delete Me")

    response = api_client.delete(reverse("document-retrieve-update-destroy", kwargs={"pk": document.id}))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Document.objects.filter(pk=document.id).exists()


@pytest.mark.django_db
@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
@patch("documents.views.get_documents_storage_client")
def test_document_download_url_returns_signed_url(mock_storage, api_client, professional):
    mock_client = Mock()
    mock_client.presign_get.return_value = (
        "https://minio.example.com/bayleaf-documents/org/uuid/documents/uuid/uuid/file.pdf?X-Amz-Expires=900"
    )
    mock_storage.return_value = mock_client

    api_client.force_authenticate(user=professional)
    organization = Organization.objects.create(name=professional.email, code="doc-org-6")
    professional.organizations.add(organization)
    document = _make_document(organization, doc_key="download-key", name="Download Doc")

    response = api_client.get(reverse("document-download-url", kwargs={"pk": document.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["url"].startswith("https://minio.example.com/")
    assert response.data["expires_in"] == 900


@pytest.mark.django_db
def test_document_create_requires_reference_or_file(api_client, professional):
    api_client.force_authenticate(user=professional)

    response = api_client.post(
        reverse("document-list-create"),
        data={"description": "No file or reference sent"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["reference"][0] == "Either 'reference' or 'file' must be provided."


@pytest.mark.django_db
def test_document_create_requires_mime_type_for_reference_only(api_client, professional):
    api_client.force_authenticate(user=professional)

    response = api_client.post(
        reverse("document-list-create"),
        data={"reference": "https://records.hospital.org/patient/12345/ecg.pdf"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["mime_type"][0] == "This field is required when no file is uploaded."
