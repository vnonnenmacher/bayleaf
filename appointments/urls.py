from django.urls import include, path
from .views import AppointmentActionViewSet, AppointmentBookingView, AvailableSlotsView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("", AppointmentActionViewSet, basename="appointment-actions")

urlpatterns = [
    path("available-slots/", AvailableSlotsView.as_view(), name="available_slots"),
    path("book/", AppointmentBookingView.as_view(), name="book-appointment"),
    path("", include(router.urls)),
]
