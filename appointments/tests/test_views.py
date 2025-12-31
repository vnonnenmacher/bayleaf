from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from appointments.models import Appointment
from professionals.models import ServiceSlot


@pytest.mark.django_db
def test_available_slots_requires_services(api_client):
    url = reverse("available_slots")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Missing required services parameter."


@pytest.mark.django_db
def test_available_slots_rejects_invalid_dates(api_client, service):
    url = reverse("available_slots")

    response = api_client.get(url, {"services": [service.id], "start_date": "2024-99-99"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Invalid date format. Use YYYY-MM-DD."


@pytest.mark.django_db
def test_available_slots_excludes_booked(api_client, service, future_slot, second_future_slot, patient, professional_user):
    Appointment.objects.create(
        professional=future_slot.shift.professional,
        patient=patient,
        service=future_slot.shift.service,
        service_slot=future_slot,
        scheduled_to=future_slot.start_time,
        duration_minutes=30,
        created_by=professional_user,
    )

    url = reverse("available_slots")
    response = api_client.get(url, {"services": [service.id]})

    assert response.status_code == status.HTTP_200_OK
    slot_ids = {slot["id"] for slot in response.data["results"]}
    assert future_slot.id not in slot_ids
    assert second_future_slot.id in slot_ids


@pytest.mark.django_db
def test_book_appointment_creates_appointment(api_client, patient_user, patient, future_slot):
    api_client.force_authenticate(user=patient_user)
    url = reverse("book-appointment")

    response = api_client.post(url, data={"service_slot_id": future_slot.id}, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    appointment = Appointment.objects.get(id=response.data["id"])
    assert appointment.patient == patient
    assert appointment.professional == future_slot.shift.professional
    assert appointment.service == future_slot.shift.service
    assert appointment.service_slot == future_slot
    assert appointment.created_by_id == patient_user.id
    assert appointment.event_type == "appointment"


@pytest.mark.django_db
def test_book_appointment_rejects_non_patient(api_client, user, future_slot):
    api_client.force_authenticate(user=user)
    url = reverse("book-appointment")

    response = api_client.post(url, data={"service_slot_id": future_slot.id}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Authenticated user is not a patient." in str(response.data)


@pytest.mark.django_db
def test_book_appointment_rejects_past_slot(api_client, patient_user, shift):
    past_start = timezone.now() - timedelta(hours=1)
    past_end = past_start + timedelta(minutes=shift.slot_duration)
    past_slot = ServiceSlot.objects.create(shift=shift, start_time=past_start, end_time=past_end)
    api_client.force_authenticate(user=patient_user)
    url = reverse("book-appointment")

    response = api_client.post(url, data={"service_slot_id": past_slot.id}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Slot must be in the future." in str(response.data)


@pytest.mark.django_db
def test_book_appointment_rejects_booked_slot(
    api_client,
    patient_user,
    patient,
    professional_user,
    future_slot,
):
    Appointment.objects.create(
        professional=future_slot.shift.professional,
        patient=patient,
        service=future_slot.shift.service,
        service_slot=future_slot,
        scheduled_to=future_slot.start_time,
        duration_minutes=30,
        created_by=professional_user,
    )
    api_client.force_authenticate(user=patient_user)
    url = reverse("book-appointment")

    response = api_client.post(url, data={"service_slot_id": future_slot.id}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already booked" in str(response.data)


@pytest.mark.django_db
def test_confirm_appointment_requires_doctor(api_client, appointment, patient_user):
    api_client.force_authenticate(user=patient_user)
    url = reverse("appointment-actions-confirm", kwargs={"pk": appointment.id})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not allowed" in response.data["detail"].lower()


@pytest.mark.django_db
def test_confirm_appointment_as_doctor(api_client, appointment):
    api_client.force_authenticate(user=appointment.professional.user_ptr)
    url = reverse("appointment-actions-confirm", kwargs={"pk": appointment.id})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    appointment.refresh_from_db()
    assert appointment.status == "CONFIRMED"
    assert response.data["status"] == "CONFIRMED"


@pytest.mark.django_db
def test_cancel_appointment_as_patient(api_client, appointment, patient_user):
    api_client.force_authenticate(user=patient_user)
    url = reverse("appointment-actions-cancel", kwargs={"pk": appointment.id})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    appointment.refresh_from_db()
    assert appointment.status == "CANCELED"


@pytest.mark.django_db
def test_complete_appointment_from_requested_rejected(api_client, appointment):
    api_client.force_authenticate(user=appointment.professional.user_ptr)
    url = reverse("appointment-actions-complete", kwargs={"pk": appointment.id})

    response = api_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid status transition" in response.data["error"]
