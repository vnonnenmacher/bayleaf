import csv
import os
from django.core.management.base import BaseCommand
from medications.models import Medication
from django.conf import settings


class Command(BaseCommand):
    help = "Loads medications from a CSV file into the Medication table."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to the CSV file containing medication names. Default: medications_clean.csv",
            default="medications.csv"
        )

    def handle(self, *args, **options):
        file_path = options["file"]

        # Full path assuming it's in the same folder as the command file
        full_path = os.path.join(
            settings.BASE_DIR, "medications", "management", "commands", file_path
        )

        if not os.path.exists(full_path):
            self.stderr.write(self.style.ERROR(f"File not found: {full_path}"))
            return

        with open(full_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            created = 0

            for row in reader:
                name = row.get("name", "").strip()
                if name:
                    obj, was_created = Medication.objects.get_or_create(name=name)
                    if was_created:
                        created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} medications created."))
