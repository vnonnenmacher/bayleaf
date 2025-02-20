from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorCreateView, DoctorRetrieveView, ShiftViewSet

router = DefaultRouter()
router.register("shifts", ShiftViewSet, basename="shifts")

urlpatterns = [
    path("register/", DoctorCreateView.as_view(), name="doctor-register"),
    path("retrieve/", DoctorRetrieveView.as_view(), name="doctor-retrieve"),
    path("", include(router.urls)),
]
