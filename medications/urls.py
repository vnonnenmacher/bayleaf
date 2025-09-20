from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet, MedicationPrescribeView, MyMedicationsView

router = DefaultRouter()
router.register("", MedicationViewSet, basename="medications")

urlpatterns = [
    path("my-medications/", MyMedicationsView.as_view(), name="my-medications"),
    path("prescribe/", MedicationPrescribeView.as_view(), name="medication-prescribe"),
] + router.urls
