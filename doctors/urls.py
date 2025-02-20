from django.urls import path
from .views import DoctorCreateView, DoctorRetrieveView

urlpatterns = [
    path("register/", DoctorCreateView.as_view(), name="doctor-register"),
    path("retrieve/", DoctorRetrieveView.as_view(), name="doctor-retrieve"),
]
