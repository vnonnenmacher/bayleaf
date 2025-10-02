from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    MedicationViewSet,
    MedicationPrescribeView,
    MyMedicationsView,
    MyMedicationItemCreateView,
    MyMedicationItemDetailView
)

router = DefaultRouter()
router.register("", MedicationViewSet, basename="medications")

urlpatterns = [
    path("my-medications/", MyMedicationsView.as_view(), name="my-medications"),
    path("my-medications/add/", MyMedicationItemCreateView.as_view(), name="my-medications-add"),
    path("my-medications/<int:id>/", MyMedicationItemDetailView.as_view(), name="my-medications-detail"),  # GET/PATCH/PUT/DELETE
    path("prescribe/", MedicationPrescribeView.as_view(), name="medication-prescribe"),
] + router.urls
