from django.urls import path, include
from rest_framework.routers import DefaultRouter

from patients.views import PatientUpdateView
from .views import DoctorCreateView, DoctorRetrieveView, DoctorUpdateView, ShiftViewSet

router = DefaultRouter()
router.register("shifts", ShiftViewSet, basename="shifts")

urlpatterns = [
    path("register/", DoctorCreateView.as_view(), name="doctor-register"),
    path("retrieve/", DoctorRetrieveView.as_view(), name="doctor-retrieve"),
    path("profile/", DoctorUpdateView.as_view(), name="update_doctor"),
    path("", include(router.urls)),
]
