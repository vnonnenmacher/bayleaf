from django.urls import path
from .views import NextAppointmentsView, PatientAppointmentListView, PatientCreateView, PatientListView, PatientRetrieveView, PatientUpdateView

urlpatterns = [
    path("register/", PatientCreateView.as_view(), name="patient-register"),
    path("retrieve/", PatientRetrieveView.as_view(), name="patient-retrieve"),
    path("profile/", PatientUpdateView.as_view(), name="update_patient"),
    path("appointments/next/", NextAppointmentsView.as_view(), name="patient-next-appointments"),
    path("appointments/", PatientAppointmentListView.as_view(), name="patient-appointments"),
    path("", PatientListView.as_view(), name="patient-list"),
]
