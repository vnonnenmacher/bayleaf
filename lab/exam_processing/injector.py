import re

from django.db import transaction

from lab.exam_processing.processor import ExamProcessor
from lab.models import AnalyteCode, AnalyteResult, MeasurementUnit, RequestedExam, Sample

_ANALYTE_REF_RE = re.compile(r"analyte_code_result\((\d+)\)\.\w+")


class AnalyteResultInjector:
    """
    Creates analyte results and triggers exam processing for a sample.
    """

    def inject(
        self,
        *,
        equipment_code: str,
        analyte_code: str,
        raw_result: str,
        sample_id=None,
        numeric_value=None,
        units_code: str | None = None,
        metadata: dict | None = None,
    ) -> AnalyteResult:
        if not equipment_code:
            raise ValueError("equipment_code is required.")
        if not analyte_code:
            raise ValueError("analyte_code is required.")
        if raw_result is None:
            raise ValueError("raw_result is required.")

        analyte_code_obj = (
            AnalyteCode.objects.select_related("analyte", "equipment")
            .filter(code=analyte_code, equipment__code=equipment_code)
            .first()
        )
        if analyte_code_obj is None:
            raise ValueError("Analyte code not found for equipment.")

        sample = None
        if sample_id is not None:
            sample = Sample.objects.filter(id=sample_id).first()
            if sample is None:
                raise ValueError("Sample not found.")
        else:
            sample = self._find_pending_sample(analyte_code_obj)
            if sample is None:
                raise ValueError("No pending sample found for analyte code.")

        return self.inject_for_sample(
            sample=sample,
            analyte_code=analyte_code_obj,
            raw_result=raw_result,
            numeric_value=numeric_value,
            units_code=units_code,
            metadata=metadata,
        )

    def inject_for_sample(
        self,
        *,
        sample: Sample,
        analyte_code: AnalyteCode,
        raw_result: str,
        numeric_value=None,
        units_code: str | None = None,
        metadata: dict | None = None,
    ) -> AnalyteResult:
        units = None
        if units_code:
            units = MeasurementUnit.objects.filter(code=units_code).first()
            if units is None:
                raise ValueError("Measurement unit not found.")

        if numeric_value is None:
            numeric_value = self._coerce_numeric(raw_result)
        else:
            numeric_value = self._coerce_numeric(numeric_value)

        with transaction.atomic():
            analyte_result = AnalyteResult.objects.create(
                analyte=analyte_code.analyte,
                equipment=analyte_code.equipment,
                sample=sample,
                raw_value=str(raw_result),
                numeric_value=numeric_value,
                units=units,
                metadata=metadata,
            )
            ExamProcessor().compute_sample(sample)

        return analyte_result

    def _find_pending_sample(self, analyte_code: AnalyteCode) -> Sample | None:
        requested_exams = (
            RequestedExam.objects.filter(is_completed=False, sample__isnull=False)
            .select_related("sample", "exam_version")
            .prefetch_related("exam_version__fields")
        )
        for requested_exam in requested_exams:
            if not self._exam_expects_analyte_code(requested_exam, analyte_code.id):
                continue
            if not AnalyteResult.objects.filter(
                sample=requested_exam.sample,
                analyte=analyte_code.analyte,
                equipment=analyte_code.equipment,
            ).exists():
                return requested_exam.sample
        return None

    def _exam_expects_analyte_code(self, requested_exam: RequestedExam, analyte_code_id: int) -> bool:
        for exam_field in requested_exam.exam_version.fields.all():
            if analyte_code_id in self._extract_analyte_code_ids(exam_field.formula):
                return True
        return False

    def _extract_analyte_code_ids(self, formula) -> set[int]:
        if not formula or not isinstance(formula, list):
            return set()
        analyte_ids: set[int] = set()
        for rule in formula:
            if not isinstance(rule, dict):
                continue
            for key in ("condition", "result"):
                expr = rule.get(key)
                if not isinstance(expr, str):
                    continue
                for match in _ANALYTE_REF_RE.finditer(expr):
                    analyte_ids.add(int(match.group(1)))
        return analyte_ids

    def _coerce_numeric(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
