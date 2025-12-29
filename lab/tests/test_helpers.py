import pytest

from lab.helpers.exam_request_helper import ExamRequestHelper
from lab.models import Exam, ExamVersion, RequestedExam, Sample


@pytest.mark.django_db
def test_create_exam_request_creates_samples_and_requested_exams(
    patient,
    professional,
    sample_type,
):
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
        notes="fasted",
    )

    samples = Sample.objects.filter(exam_request=exam_request)
    requested_exams = RequestedExam.objects.filter(exam_request=exam_request)

    assert samples.count() == 1
    assert requested_exams.count() == 2
    assert exam_request.notes == "fasted"
    assert all(requested_exam.sample for requested_exam in requested_exams)


@pytest.mark.django_db
def test_create_exam_request_with_no_versions_creates_only_request(
    patient,
    professional,
):
    helper = ExamRequestHelper()
    exam_request = helper.create_exam_request(
        patient=patient,
        requested_by=professional,
        exam_versions=[],
        notes="no exams",
    )

    assert ExamVersion.objects.count() == 0
    assert Sample.objects.filter(exam_request=exam_request).count() == 0
    assert RequestedExam.objects.filter(exam_request=exam_request).count() == 0
    assert exam_request.notes == "no exams"


@pytest.mark.django_db
def test_cancel_exam_request_sets_fields(exam_request, professional):
    helper = ExamRequestHelper()

    helper.cancel_exam_request(
        exam_request=exam_request,
        canceled_by=professional,
        reason="duplicate",
    )

    exam_request.refresh_from_db()
    assert exam_request.canceled_at is not None
    assert exam_request.canceled_by == professional
    assert exam_request.cancel_reason == "duplicate"


@pytest.mark.django_db
def test_cancel_exam_request_keeps_reason_when_none(exam_request, professional):
    exam_request.cancel_reason = "keep"
    exam_request.save(update_fields=["cancel_reason"])

    helper = ExamRequestHelper()
    helper.cancel_exam_request(
        exam_request=exam_request,
        canceled_by=professional,
        reason=None,
    )

    exam_request.refresh_from_db()
    assert exam_request.cancel_reason == "keep"


@pytest.mark.django_db
def test_cancel_exam_request_requires_professional(exam_request):
    helper = ExamRequestHelper()

    with pytest.raises(ValueError, match="professional must cancel"):
        helper.cancel_exam_request(
            exam_request=exam_request,
            canceled_by=None,
        )


@pytest.mark.django_db
def test_cancel_exam_request_rejects_double_cancel(exam_request, professional):
    helper = ExamRequestHelper()
    helper.cancel_exam_request(
        exam_request=exam_request,
        canceled_by=professional,
    )

    with pytest.raises(ValueError, match="already canceled"):
        helper.cancel_exam_request(
            exam_request=exam_request,
            canceled_by=professional,
        )
