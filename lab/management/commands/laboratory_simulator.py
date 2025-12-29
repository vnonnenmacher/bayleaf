import random
import re
import time

from django.core.management.base import BaseCommand

from lab.exam_processing.injector import AnalyteResultInjector
from lab.models import AnalyteCode, AnalyteResult, RequestedExam

_ANALYTE_REF_RE = re.compile(r"analyte_code_result\((\d+)\)\.\w+")


class Command(BaseCommand):
    help = "Simulate equipment analyte results for pending requested exams."

    def add_arguments(self, parser):
        parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run.")
        parser.add_argument("--interval", type=int, default=5, help="Seconds between iterations.")
        parser.add_argument("--chance", type=float, default=0.3, help="Chance for each pending analyte.")

    def handle(self, *args, **options):
        iterations = max(int(options["iterations"]), 1)
        interval = max(int(options["interval"]), 0)
        chance = float(options["chance"])

        for idx in range(iterations):
            created, pending = self._run_iteration(chance)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Iteration {idx + 1}: {created} results created. Pending analytes: {pending}."
                )
            )
            if idx < iterations - 1 and interval:
                time.sleep(interval)

    def _run_iteration(self, chance: float) -> tuple[int, int]:
        injector = AnalyteResultInjector()
        requested_exams = (
            RequestedExam.objects.filter(is_completed=False, sample__isnull=False)
            .select_related("sample", "exam_version")
            .prefetch_related("exam_version__fields")
        )
        created = 0
        pending_total = 0
        for requested_exam in requested_exams:
            pending_analytes = self._pending_analyte_codes(requested_exam)
            pending_total += len(pending_analytes)
            for analyte_code in pending_analytes:
                if random.random() > chance:
                    continue
                raw_value = f"{random.uniform(0.1, 10.0):.2f}"
                injector.inject_for_sample(
                    sample=requested_exam.sample,
                    analyte_code=analyte_code,
                    raw_result=raw_value,
                    numeric_value=float(raw_value),
                )
                created += 1
        return created, pending_total

    def _pending_analyte_codes(self, requested_exam: RequestedExam) -> list[AnalyteCode]:
        analyte_ids = set()
        for exam_field in requested_exam.exam_version.fields.all():
            formula = exam_field.formula
            if not formula or not isinstance(formula, list):
                continue
            for rule in formula:
                if not isinstance(rule, dict):
                    continue
                for key in ("condition", "result"):
                    expr = rule.get(key)
                    if not isinstance(expr, str):
                        continue
                    for match in _ANALYTE_REF_RE.finditer(expr):
                        analyte_ids.add(int(match.group(1)))

        if not analyte_ids:
            return []

        analyte_codes = (
            AnalyteCode.objects.select_related("analyte", "equipment")
            .filter(id__in=analyte_ids)
            .order_by("id")
        )
        pending = []
        for analyte_code in analyte_codes:
            exists = AnalyteResult.objects.filter(
                sample=requested_exam.sample,
                analyte=analyte_code.analyte,
                equipment=analyte_code.equipment,
            ).exists()
            if not exists:
                pending.append(analyte_code)
        return pending
