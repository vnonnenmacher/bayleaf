from django.urls import include, path
from .views import (
    AppointmentActionViewSet,
    AppointmentBookingView,
    AvailableSlotsView,
    AvailableSpecializationsView,
    AvailableProfessionalsView,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("", AppointmentActionViewSet, basename="appointment-actions")

urlpatterns = [
    path("available-slots/", AvailableSlotsView.as_view(), name="available_slots"),
    path("available-specializations/", AvailableSpecializationsView.as_view(), name="available_specializations"),
    path("available-professionals/", AvailableProfessionalsView.as_view(), name="available_professionals"),
    path("book/", AppointmentBookingView.as_view(), name="book-appointment"),
    path("", include(router.urls)),
]
