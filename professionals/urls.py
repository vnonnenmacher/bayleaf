from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProfessionalCreateView, ProfessionalRetrieveView, ProfessionalUpdateView, ShiftViewSet

router = DefaultRouter()
router.register("shifts", ShiftViewSet, basename="shifts")

urlpatterns = [
    path("register/", ProfessionalCreateView.as_view(), name="professional-register"),
    path("retrieve/", ProfessionalRetrieveView.as_view(), name="professional-retrieve"),
    path("profile/", ProfessionalUpdateView.as_view(), name="update_professional"),
    path("", include(router.urls)),
]
