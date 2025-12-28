import random
import time

from django.core.management.base import BaseCommand

from lab.helpers.exam_request_helper import ExamRequestHelper
from lab.models import ExamRequest, ExamVersion
from patients.models import Patient
from professionals.models import Professional


class Command(BaseCommand):
    help = "Simulate exam requests in a loop."

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval-seconds",
            type=int,
            default=10,
            help="Seconds to wait between iterations (default 10).",
        )
        parser.add_argument(
            "--chance",
            type=float,
            default=10.0,
            help="Percent chance per iteration to create a request (default 10).",
        )
        parser.add_argument(
            "--min-exams",
            type=int,
            default=1,
            help="Minimum number of exams per request (default 1).",
        )
        parser.add_argument(
            "--max-exams",
            type=int,
            default=4,
            help="Maximum number of exams per request (default 4).",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single iteration and exit.",
        )

    def handle(self, *args, **options):
        interval = max(1, int(options["interval_seconds"]))
        chance = float(options["chance"])
        min_exams = max(1, int(options["min_exams"]))
        max_exams = max(min_exams, int(options["max_exams"]))
        run_once = options["once"]

        self.stdout.write(self.style.SUCCESS("Starting exam requester loop..."))

        try:
            while True:
                self._run_iteration(chance=chance, min_exams=min_exams, max_exams=max_exams)
                if run_once:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Exam requester stopped by user."))

    def _run_iteration(self, *, chance: float, min_exams: int, max_exams: int) -> None:
        professionals = list(Professional.objects.all())
        patients = list(Patient.objects.all())
        exam_versions = list(ExamVersion.objects.filter(is_active=True).select_related("exam__material"))

        if not professionals or not patients or not exam_versions:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping iteration: need professionals, patients, and active exam versions."
                )
            )
            return

        created_count = 0
        helper = ExamRequestHelper()

        self._maybe_cancel_requests(helper)

        for professional in professionals:
            roll = random.uniform(0, 100)
            if roll > chance:
                continue

            patient = random.choice(patients)
            count = random.randint(min_exams, max_exams)
            count = min(count, len(exam_versions))

            chosen_exams = random.sample(exam_versions, count)
            exam_request = helper.create_exam_request(
                patient=patient,
                requested_by=professional,
                exam_versions=chosen_exams,
            )
            created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created exam request {exam_request.id} by {professional.id} "
                    f"for patient {patient.id} with {count} exams."
                )
            )

        if created_count == 0:
            self.stdout.write("No requests created this iteration.")

    def _maybe_cancel_requests(self, helper: ExamRequestHelper) -> None:
        active_requests = ExamRequest.objects.filter(canceled_at__isnull=True).select_related("requested_by")
        canceled_count = 0

        for exam_request in active_requests:
            if random.uniform(0, 100) > 1.0:
                continue
            try:
                helper.cancel_exam_request(
                    exam_request=exam_request,
                    canceled_by=exam_request.requested_by,
                    reason="Auto-canceled by simulation.",
                )
                canceled_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Canceled exam request {exam_request.id} (simulation).")
                )
            except ValueError:
                continue

        if canceled_count:
            self.stdout.write(self.style.WARNING(f"Canceled {canceled_count} exam request(s) this iteration."))
