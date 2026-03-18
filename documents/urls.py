from django.urls import path

from documents.views import (
    DocumentDownloadURLView,
    DocumentListCreateView,
    DocumentRetrieveUpdateDestroyView,
)


urlpatterns = [
    path("", DocumentListCreateView.as_view(), name="document-list-create"),
    path("<uuid:pk>/", DocumentRetrieveUpdateDestroyView.as_view(), name="document-retrieve-update-destroy"),
    path("<uuid:pk>/download-url/", DocumentDownloadURLView.as_view(), name="document-download-url"),
]
