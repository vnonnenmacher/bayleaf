from django.urls import path
from .views import PatientCreateView, PatientRetrieveView, PatientUpdateView

urlpatterns = [
    path("register/", PatientCreateView.as_view(), name="patient-register"),
    path("retrieve/", PatientRetrieveView.as_view(), name="patient-retrieve"),
    path("profile/", PatientUpdateView.as_view(), name="update_patient"),    
]
