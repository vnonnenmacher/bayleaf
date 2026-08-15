from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from lab.helpers.exam_request_helper import ExamRequestHelper
from lab.models import (
    Equipment,
    EquipmentGroup,
    Exam,
    ExamField,
    ExamFieldResult,
    ExamVersion,
    MeasurementUnit,
    RequestedExam,
    SampleState,
    SampleStateTransition,
    Sector,
)


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


@pytest.mark.django_db
def test_sector_term_search_returns_filtered_results(api_client, professional):
    api_client.force_authenticate(user=professional)
    Sector.objects.create(name="Bioquimica", description="desc")
    Sector.objects.create(name="Parasitologia", description="desc")

    url = reverse("sector-term-search")
    response = api_client.get(url, {"term": "bio"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Bioquimica"


@pytest.mark.django_db
def test_equipment_term_search_returns_filtered_results(api_client, professional):
    api_client.force_authenticate(user=professional)
    group = EquipmentGroup.objects.create(name="Chemistry")
    Equipment.objects.create(name="Cobas 6000", code="COB6000", group=group)
    Equipment.objects.create(name="Sysmex XN", code="XN", group=group)

    url = reverse("equipment-term-search")
    response = api_client.get(url, {"term": "cob"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Cobas 6000"


@pytest.mark.django_db
def test_sector_term_search_requires_term(api_client, professional):
    api_client.force_authenticate(user=professional)
    url = reverse("sector-term-search")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Missing search term"


@pytest.mark.django_db
def test_search_exam_requests_filters_by_is_completed_and_prunes_tree(
    api_client,
    professional,
    patient,
    sample_type,
):
    api_client.force_authenticate(user=professional)

    requested_state = SampleState.objects.create(name="Requested", is_initial_state=True)

    exam_one = Exam.objects.create(
        name="Glucose",
        code="GLU",
        description="Glucose exam",
        material=sample_type,
    )
    exam_two = Exam.objects.create(
        name="Cholesterol",
        code="CHOL",
        description="Cholesterol exam",
        material=sample_type,
    )
    version_one = ExamVersion.objects.create(exam=exam_one, version=1, is_active=True)
    version_two = ExamVersion.objects.create(exam=exam_two, version=1, is_active=True)

    helper = ExamRequestHelper()
    exam_request = helper.create_exam_request(
        patient=patient,
        requested_by=professional,
        exam_versions=[version_one, version_two],
        code="REQ-1001",
        notes="fasting",
    )

    sample = exam_request.samples.first()
    SampleStateTransition.objects.create(
        sample=sample,
        previous_state=None,
        new_state=requested_state,
        changed_by=professional,
        transaction_hash="hash-req-1001",
        is_verified=True,
    )

    first_requested_exam = RequestedExam.objects.get(exam_request=exam_request, exam_version=version_one)
    first_requested_exam.is_completed = True
    first_requested_exam.save(update_fields=["is_completed"])

    url = reverse("examrequest-search-exam-requests")
    response = api_client.get(url, {"is_completed": "true"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1

    result = response.data["results"][0]
    assert result["request"]["code"] == "REQ-1001"
    assert result["request"]["patient"]["first_name"] == patient.first_name
    assert result["request"]["patient"]["birth_date"] == str(patient.birth_date)

    assert len(result["samples"]) == 1
    assert len(result["samples"][0]["exams"]) == 1
    assert result["samples"][0]["exams"][0]["is_completed"] is True
    assert result["samples"][0]["exams"][0]["exam"]["code"] == "GLU"


@pytest.mark.django_db
def test_search_exam_requests_filters_by_sample_status(api_client, professional, patient, sample_type):
    api_client.force_authenticate(user=professional)

    requested_state = SampleState.objects.create(name="Requested", is_initial_state=True)
    processing_state = SampleState.objects.create(name="Processing")

    exam = Exam.objects.create(
        name="Triglycerides",
        code="TRI",
        description="Triglycerides exam",
        material=sample_type,
    )
    version = ExamVersion.objects.create(exam=exam, version=1, is_active=True)

    helper = ExamRequestHelper()
    exam_request = helper.create_exam_request(
        patient=patient,
        requested_by=professional,
        exam_versions=[version],
        code="REQ-2001",
    )

    sample = exam_request.samples.first()
    SampleStateTransition.objects.create(
        sample=sample,
        previous_state=None,
        new_state=requested_state,
        changed_by=professional,
        transaction_hash="hash-req-2001-a",
        is_verified=True,
    )
    SampleStateTransition.objects.create(
        sample=sample,
        previous_state=requested_state,
        new_state=processing_state,
        changed_by=professional,
        transaction_hash="hash-req-2001-b",
        is_verified=True,
    )

    url = reverse("examrequest-search-exam-requests")
    response = api_client.get(url, {"sample_status": str(processing_state.id)})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    result = response.data["results"][0]
    assert result["request"]["code"] == "REQ-2001"
    assert result["samples"][0]["current_state"]["name"] == "Processing"


# ---------------------------------------------------------------------------
# fetch-results
# ---------------------------------------------------------------------------

def _make_exam_request(patient, professional, sample_type, code):
    from lab.helpers.exam_request_helper import ExamRequestHelper
    exam = Exam.objects.create(name=f"Exam {code}", code=code, description="", material=sample_type)
    version = ExamVersion.objects.create(exam=exam, version=1, is_active=True)
    helper = ExamRequestHelper()
    return helper.create_exam_request(
        patient=patient,
        requested_by=professional,
        exam_versions=[version],
        code=f"REQ-{code}",
    ), version


@pytest.mark.django_db
def test_fetch_results_requires_at_least_one_filter(api_client, professional):
    api_client.force_authenticate(user=professional)
    url = reverse("examrequest-fetch-results")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data


@pytest.mark.django_db
def test_fetch_results_by_request_id(api_client, professional, patient, sample_type):
    api_client.force_authenticate(user=professional)
    exam_request, version = _make_exam_request(patient, professional, sample_type, "GLU")

    unit = MeasurementUnit.objects.create(name="mg/dL", code="MG_DL")
    field = ExamField.objects.create(
        exam_version=version,
        name="Result",
        code="RES",
        field_type="decimal",
        measurement_unit=unit,
    )
    req_exam = RequestedExam.objects.get(exam_request=exam_request)
    ExamFieldResult.objects.create(
        requested_exam=req_exam,
        exam_field=field,
        raw_value="5.40",
        computed_value="5.40",
        classification="normal",
    )

    url = reverse("examrequest-fetch-results")
    response = api_client.get(url, {"request_ids": exam_request.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    result = response.data[0]
    assert result["request"]["code"] == "REQ-GLU"
    assert len(result["samples"]) == 1
    exams = result["samples"][0]["exams"]
    assert len(exams) == 1
    assert exams[0]["exam"]["code"] == "GLU"
    field_results = exams[0]["field_results"]
    assert len(field_results) == 1
    assert field_results[0]["raw_value"] == "5.40"
    assert field_results[0]["measurement_unit"]["code"] == "MG_DL"


@pytest.mark.django_db
def test_fetch_results_by_sample_id(api_client, professional, patient, sample_type):
    api_client.force_authenticate(user=professional)
    exam_request, _ = _make_exam_request(patient, professional, sample_type, "NA")

    sample = exam_request.samples.first()
    url = reverse("examrequest-fetch-results")
    response = api_client.get(url, {"sample_ids": str(sample.id)})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert str(response.data[0]["samples"][0]["id"]) == str(sample.id)


@pytest.mark.django_db
def test_fetch_results_by_requested_exam_id(api_client, professional, patient, sample_type):
    api_client.force_authenticate(user=professional)
    exam_request, _ = _make_exam_request(patient, professional, sample_type, "CRP")

    req_exam = RequestedExam.objects.get(exam_request=exam_request)
    url = reverse("examrequest-fetch-results")
    response = api_client.get(url, {"requested_exam_ids": req_exam.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["samples"][0]["exams"][0]["requested_exam_id"] == req_exam.id


@pytest.mark.django_db
def test_fetch_results_blocks_non_professional(api_client, user):
    api_client.force_authenticate(user=user)
    url = reverse("examrequest-fetch-results")
    response = api_client.get(url, {"request_ids": "1"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_fetch_results_filters_by_is_completed(api_client, professional, patient, sample_type):
    api_client.force_authenticate(user=professional)
    exam_request, _ = _make_exam_request(patient, professional, sample_type, "KFILT")

    req_exam = RequestedExam.objects.get(exam_request=exam_request)
    req_exam.is_completed = True
    req_exam.save(update_fields=["is_completed"])

    url = reverse("examrequest-fetch-results")
    response_true = api_client.get(url, {"request_ids": exam_request.id, "is_completed": "true"})
    response_false = api_client.get(url, {"request_ids": exam_request.id, "is_completed": "false"})

    assert response_true.status_code == status.HTTP_200_OK
    assert len(response_true.data[0]["samples"][0]["exams"]) == 1

    assert response_false.status_code == status.HTTP_200_OK
    # sample is pruned because no exams match, so the request has an empty samples list
    assert response_false.data[0]["samples"] == []


@pytest.mark.django_db
def test_fetch_results_filters_by_is_validated(api_client, professional, patient, sample_type):
    api_client.force_authenticate(user=professional)
    exam_request, _ = _make_exam_request(patient, professional, sample_type, "VFILT")

    url = reverse("examrequest-fetch-results")
    response_not_validated = api_client.get(url, {"request_ids": exam_request.id, "is_validated": "false"})
    response_validated = api_client.get(url, {"request_ids": exam_request.id, "is_validated": "true"})

    assert response_not_validated.status_code == status.HTTP_200_OK
    assert len(response_not_validated.data) == 1
    assert response_not_validated.data[0]["request"]["is_validated"] is False

    assert response_validated.status_code == status.HTTP_200_OK
    assert len(response_validated.data) == 0
