from django.urls import path
from .views import AppointmentBookingView, AvailableSlotsView

urlpatterns = [
    path("available-slots/", AvailableSlotsView.as_view(), name="available_slots"),
     path("book/", AppointmentBookingView.as_view(), name="book-appointment"),
]
