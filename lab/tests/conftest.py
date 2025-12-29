import pytest
from django.contrib.auth import get_user_model

from lab.models import (
    AllowedStateTransition,
    Exam,
    ExamRequest,
    ExamVersion,
    Sample,
    SampleState,
    SampleStateTransition,
    SampleType,
)
from patients.models import Patient
from professionals.models import Professional
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(email="user@example.com", password="password")


@pytest.fixture
def professional(db):
    return Professional.objects.create(
        email="pro@example.com",
        first_name="Pro",
        last_name="User",
        password="password",
    )


@pytest.fixture
def patient(db):
    return Patient.objects.create(
        email="patient@example.com",
        first_name="Pat",
        last_name="Ent",
        password="password",
    )


@pytest.fixture
def sample_type(db):
    return SampleType.objects.create(name="Blood")


@pytest.fixture
def initial_sample_state(db):
    return SampleState.objects.create(name="Requested", is_initial_state=True)


@pytest.fixture
def processing_sample_state(db):
    return SampleState.objects.create(name="Processing")


@pytest.fixture
def sample(db, patient, sample_type):
    return Sample.objects.create(patient=patient, sample_type=sample_type)


@pytest.fixture
def sample_with_initial_transition(db, sample, initial_sample_state, professional):
    SampleStateTransition.objects.create(
        sample=sample,
        previous_state=None,
        new_state=initial_sample_state,
        changed_by=professional,
        transaction_hash="hash",
        is_verified=True,
    )
    return sample


@pytest.fixture
def allowed_transition(db, initial_sample_state, processing_sample_state):
    return AllowedStateTransition.objects.create(
        from_state=initial_sample_state,
        to_state=processing_sample_state,
    )


@pytest.fixture
def exam(db, sample_type):
    return Exam.objects.create(
        name="Glucose",
        code="GLU",
        description="Glucose exam",
        material=sample_type,
    )


@pytest.fixture
def exam_version(db, exam):
    return ExamVersion.objects.create(exam=exam, version=1, is_active=True)


@pytest.fixture
def exam_request(db, patient, professional):
    return ExamRequest.objects.create(patient=patient, requested_by=professional)
