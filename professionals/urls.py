from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (ProfessionalAppointmentListView, ProfessionalCreateView,
                    ProfessionalRetrieveView,
                    ProfessionalUpdateView,
                    ProfessionalViewSet,
                    RoleViewSet,
                    ShiftViewSet,
                    SpecializationViewSet)

router = DefaultRouter()
router.register("list", ProfessionalViewSet, basename="professionals")
router.register("shifts", ShiftViewSet, basename="shifts")
router.register("roles", RoleViewSet, basename="roles")
router.register("specializations", SpecializationViewSet, basename="specializations")

urlpatterns = [
    path("register/", ProfessionalCreateView.as_view(), name="professional-register"),
    path("retrieve/", ProfessionalRetrieveView.as_view(), name="professional-retrieve"),
    path("profile/", ProfessionalUpdateView.as_view(), name="update_professional"),
    path("appointments/", ProfessionalAppointmentListView.as_view(), name="professional-appointments"),
    path("", include(router.urls)),
]
