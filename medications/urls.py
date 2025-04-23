from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import MedicationListView, MedicationSearchView


urlpatterns = [
    path("", MedicationListView.as_view(), name="medication-list"),
    path("drug-search/", MedicationSearchView.as_view(), name="medication-search"),
]
