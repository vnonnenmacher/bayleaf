from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from lab.models import SampleStateTransition


@pytest.mark.django_db
def test_request_sample_creates_transition(
    api_client,
    user,
    patient,
    sample_type,
    initial_sample_state,
):
    api_client.force_authenticate(user=user)
    url = reverse("sample-request-sample")

    response = api_client.post(
        url,
        data={"patient_uuid": str(patient.pid), "sample_type": sample_type.id},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["sample_id"]
    assert response.data["transaction_hash"]

    transitions = SampleStateTransition.objects.filter(sample_id=response.data["sample_id"])
    assert transitions.count() == 1
    transition = transitions.first()
    assert transition.new_state == initial_sample_state
    assert transition.is_verified is True


@pytest.mark.django_db
def test_request_sample_requires_authentication(api_client, patient, sample_type):
    url = reverse("sample-request-sample")

    response = api_client.post(
        url,
        data={"patient_uuid": str(patient.pid), "sample_type": sample_type.id},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_update_sample_state_requires_state_id(
    api_client,
    user,
    sample_with_initial_transition,
):
    api_client.force_authenticate(user=user)
    url = reverse("sample-update-sample-state", kwargs={"pk": sample_with_initial_transition.id})

    response = api_client.post(url, data={}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "new_state_id is required."


@pytest.mark.django_db
def test_update_sample_state_requires_authentication(api_client, sample_with_initial_transition):
    url = reverse("sample-update-sample-state", kwargs={"pk": sample_with_initial_transition.id})

    response = api_client.post(
        url,
        data={"new_state_id": "missing"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_update_sample_state_returns_not_found_for_unknown_state(
    api_client,
    user,
    sample_with_initial_transition,
):
    api_client.force_authenticate(user=user)
    url = reverse("sample-update-sample-state", kwargs={"pk": sample_with_initial_transition.id})

    response = api_client.post(
        url,
        data={"new_state_id": 9999},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"] == "New state does not exist."


@pytest.mark.django_db
def test_update_sample_state_rejects_disallowed_transition(
    api_client,
    user,
    sample_with_initial_transition,
    processing_sample_state,
):
    api_client.force_authenticate(user=user)
    url = reverse("sample-update-sample-state", kwargs={"pk": sample_with_initial_transition.id})

    response = api_client.post(
        url,
        data={"new_state_id": processing_sample_state.id},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "not allowed" in response.data["error"]


@pytest.mark.django_db
def test_update_sample_state_allows_transition(
    api_client,
    user,
    sample_with_initial_transition,
    processing_sample_state,
    allowed_transition,
):
    api_client.force_authenticate(user=user)
    url = reverse("sample-update-sample-state", kwargs={"pk": sample_with_initial_transition.id})

    response = api_client.post(
        url,
        data={"new_state_id": processing_sample_state.id},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["new_state"] == processing_sample_state.name

    transitions = SampleStateTransition.objects.filter(sample=sample_with_initial_transition)
    assert transitions.count() == 2
    assert transitions.order_by("-created_at").first().new_state == processing_sample_state


@pytest.mark.django_db
def test_exam_request_cancel_calls_helper(
    api_client,
    professional,
    exam_request,
):
    api_client.force_authenticate(user=professional)
    url = reverse("examrequest-cancel", kwargs={"pk": exam_request.id})

    with patch("lab.views.ExamRequestHelper.cancel_exam_request") as cancel_mock:
        response = api_client.post(url, data={"cancel_reason": "duplicate"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    cancel_mock.assert_called_once()
    _, kwargs = cancel_mock.call_args
    assert kwargs["exam_request"] == exam_request
    assert kwargs["canceled_by"] == professional
    assert kwargs["reason"] == "duplicate"


@pytest.mark.django_db
def test_exam_request_cancel_requires_authentication(api_client, exam_request):
    url = reverse("examrequest-cancel", kwargs={"pk": exam_request.id})

    response = api_client.post(url, data={"cancel_reason": "duplicate"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_exam_request_cancel_requires_professional(api_client, user, exam_request):
    api_client.force_authenticate(user=user)
    url = reverse("examrequest-cancel", kwargs={"pk": exam_request.id})

    response = api_client.post(url, data={"cancel_reason": "duplicate"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
