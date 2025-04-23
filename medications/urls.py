from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet

router = DefaultRouter()
router.register("", MedicationViewSet, basename="medications")

urlpatterns = router.urls