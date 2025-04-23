from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet, MedicationPrescribeView

router = DefaultRouter()
router.register("", MedicationViewSet, basename="medications")

urlpatterns = [
    path("prescribe/", MedicationPrescribeView.as_view(), name="medication-prescribe"),
] + router.urls
