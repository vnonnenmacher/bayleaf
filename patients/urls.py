# patients/urls.py
from django.urls import path

from .views import (
    # patient endpoints
    PatientCreateView,
    PatientRetrieveView,
    PatientUpdateView,
    PatientListView,
    PatientAppointmentListView,
    NextAppointmentsView,
    # relative endpoints
    RelativeCreateView,
    RelativeMeView,
    RelativeAddManagedPatientView,
    RelativeLinkExistingPatientView,
    PatientRelationshipToggleActiveView,
)

urlpatterns = [
    # ===========================
    # PATIENT ENDPOINTS
    # ===========================
    path("register/", PatientCreateView.as_view(), name="patient-register"),
    path("retrieve/", PatientRetrieveView.as_view(), name="patient-retrieve"),
    path("profile/", PatientUpdateView.as_view(), name="patient-profile"),
    path("appointments/", PatientAppointmentListView.as_view(), name="patient-appointments"),
    path("appointments/next/", NextAppointmentsView.as_view(), name="patient-next-appointments"),
    path("", PatientListView.as_view(), name="patient-list"),

    # ===========================
    # RELATIVE ENDPOINTS
    # ===========================
    # 1. Create a relative (signup)
    path("relatives/register/", RelativeCreateView.as_view(), name="relative-register"),

    # 2. Retrieve or update logged-in relative (profile + nested address/contact)
    #    GET   -> fetch full relative data + linked patients
    #    PATCH -> update profile or contacts
    path("relatives/me/", RelativeMeView.as_view(), name="relative-me"),

    # 3. Relative creates a managed patient (backend generates placeholder email)
    path("relatives/me/patients/managed/", RelativeAddManagedPatientView.as_view(),
         name="relative-add-managed-patient"),

    # 4. Relative links an existing patient
    path("relatives/me/patients/link/", RelativeLinkExistingPatientView.as_view(),
         name="relative-link-existing-patient"),

    # 5. Toggle relationship active/inactive
    path("relatives/me/relationships/<int:pk>/toggle-active/",
         PatientRelationshipToggleActiveView.as_view(),
         name="relative-relationship-toggle-active"),
]
