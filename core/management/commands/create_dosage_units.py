from django.core.management.base import BaseCommand
from core.models import DosageUnit


class Command(BaseCommand):
    help = "Creates standard dosage units in the database"

    def handle(self, *args, **kwargs):
        units = [
            "mg", "g", "mcg", "kg",
            "ml", "l",
            "tablet", "capsule", "pill", "drop", "spray", "patch", "suppository",
            "unit", "puff", "ampoule", "vial",
        ]

        created_count = 0

        for unit in units:
            obj, created = DosageUnit.objects.get_or_create(name=unit)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {created_count} dosage unit(s)."
        ))
