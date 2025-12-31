from datetime import time, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from core.models import Service
from patients.models import Patient
from professionals.models import Professional, Shift, ServiceSlot


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(email="user@example.com", password="password")


@pytest.fixture
def professional_user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(email="pro@example.com", password="password")


@pytest.fixture
def professional(db, professional_user):
    return Professional.objects.create(
        user_ptr=professional_user,
        email=professional_user.email,
        first_name="Pro",
        last_name="User",
    )


@pytest.fixture
def patient_user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(email="patient@example.com", password="password")


@pytest.fixture
def patient(db, patient_user):
    return Patient.objects.create(
        user_ptr=patient_user,
        email=patient_user.email,
        first_name="Pat",
        last_name="Ent",
    )


@pytest.fixture
def service(db):
    return Service.objects.create(name="General", code="GEN", description="General consult")


@pytest.fixture
def shift(db, professional, service):
    return Shift.objects.create(
        professional=professional,
        weekday=0,
        service=service,
        slot_duration=30,
        from_time=time(9, 0),
        to_time=time(10, 0),
    )


@pytest.fixture
def future_slot(db, shift):
    start_time = timezone.now() + timedelta(days=1)
    end_time = start_time + timedelta(minutes=shift.slot_duration)
    return ServiceSlot.objects.create(shift=shift, start_time=start_time, end_time=end_time)


@pytest.fixture
def second_future_slot(db, shift):
    start_time = timezone.now() + timedelta(days=1, hours=1)
    end_time = start_time + timedelta(minutes=shift.slot_duration)
    return ServiceSlot.objects.create(shift=shift, start_time=start_time, end_time=end_time)


@pytest.fixture
def appointment(db, professional, patient, service, professional_user):
    scheduled_to = timezone.now() + timedelta(days=2)
    return Appointment.objects.create(
        professional=professional,
        patient=patient,
        service=service,
        scheduled_to=scheduled_to,
        duration_minutes=30,
        created_by=professional_user,
    )
