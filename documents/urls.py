from django.urls import path

from documents.views import (
    DocumentFamilyListCreateView,
    DocumentFamilyRetrieveUpdateView,
    DocumentVersionDownloadURLView,
    DocumentVersionListView,
    DocumentVersionPublishView,
    DocumentVersionRetrieveView,
    DocumentVersionUploadView,
)


urlpatterns = [
    path("", DocumentFamilyListCreateView.as_view(), name="document-family-list-create"),
    path("<uuid:pk>/", DocumentFamilyRetrieveUpdateView.as_view(), name="document-family-retrieve-update"),
    path("<uuid:family_id>/versions/", DocumentVersionListView.as_view(), name="document-version-list"),
    path("<uuid:family_id>/versions/upload/", DocumentVersionUploadView.as_view(), name="document-version-upload"),
    path("versions/<uuid:pk>/", DocumentVersionRetrieveView.as_view(), name="document-version-retrieve"),
    path("versions/<uuid:pk>/publish/", DocumentVersionPublishView.as_view(), name="document-version-publish"),
    path(
        "versions/<uuid:pk>/download-url/",
        DocumentVersionDownloadURLView.as_view(),
        name="document-version-download-url",
    ),
]
