from django.db import transaction
from django.utils import timezone

from lab.models import ExamRequest, RequestedExam, Sample


class ExamRequestHelper:
    @transaction.atomic
    def create_exam_request(
        self,
        *,
        patient,
        requested_by,
        exam_versions,
        **exam_request_kwargs,
    ) -> ExamRequest:
        exam_request = ExamRequest.objects.create(
            patient=patient,
            requested_by=requested_by,
            **exam_request_kwargs,
        )

        sample_map = {}
        for exam_version in exam_versions:
            sample_type = exam_version.exam.material
            if sample_type.id not in sample_map:
                sample_map[sample_type.id] = Sample.objects.create(
                    patient=patient,
                    sample_type=sample_type,
                    exam_request=exam_request,
                )

        for exam_version in exam_versions:
            sample = sample_map.get(exam_version.exam.material.id)
            RequestedExam.objects.create(
                exam_request=exam_request,
                exam_version=exam_version,
                sample=sample,
            )

        return exam_request

    @transaction.atomic
    def cancel_exam_request(
        self,
        *,
        exam_request: ExamRequest,
        canceled_by,
        reason: str | None = None,
    ) -> ExamRequest:
        if exam_request.canceled_at:
            raise ValueError("Exam request is already canceled.")
        if canceled_by is None:
            raise ValueError("A professional must cancel the exam request.")

        exam_request.canceled_at = timezone.now()
        exam_request.canceled_by = canceled_by
        if reason is not None:
            exam_request.cancel_reason = reason
        exam_request.save(update_fields=["canceled_at", "canceled_by", "cancel_reason"])
        return exam_request
