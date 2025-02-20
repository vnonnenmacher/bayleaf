from django.urls import path
from .views import AvailableSlotsView

urlpatterns = [
    path("available-slots/", AvailableSlotsView.as_view(), name="available_slots"),
]
