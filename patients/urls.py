from django.urls import path
from .views import PatientCreateView

urlpatterns = [
    path("register/", PatientCreateView.as_view(), name="patient-register"),
]