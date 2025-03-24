from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProfessionalCreateView, ProfessionalRetrieveView, ProfessionalUpdateView, ProfessionalViewSet, RoleViewSet, ShiftViewSet

router = DefaultRouter()
router.register("", ProfessionalViewSet, basename="professionals")
router.register("shifts", ShiftViewSet, basename="shifts")
router.register("roles", RoleViewSet, basename="roles")

urlpatterns = [
    path("register/", ProfessionalCreateView.as_view(), name="professional-register"),
    path("retrieve/", ProfessionalRetrieveView.as_view(), name="professional-retrieve"),
    path("profile/", ProfessionalUpdateView.as_view(), name="update_professional"),
    path("", include(router.urls)),
]
