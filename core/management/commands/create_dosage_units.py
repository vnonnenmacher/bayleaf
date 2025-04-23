from django.core.management.base import BaseCommand
from core.models import DosageUnit


class Command(BaseCommand):
    help = "Creates standard dosage units in the database"

    def handle(self, *args, **kwargs):
        units = [
            ("mg", "milligram"),
            ("g", "gram"),
            ("mcg", "microgram"),
            ("kg", "kilogram"),
            ("ml", "milliliter"),
            ("l", "liter"),
            ("tablet", "tablet"),
            ("capsule", "capsule"),
            ("pill", "pill"),
            ("drop", "drop"),
            ("spray", "spray"),
            ("patch", "patch"),
            ("suppository", "suppository"),
            ("unit", "unit"),
            ("puff", "puff"),
            ("ampoule", "ampoule"),
            ("vial", "vial"),
        ]

        created_count = 0

        for code, name in units:
            obj, created = DosageUnit.objects.get_or_create(code=code, defaults={"name": name})
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} dosage unit(s)."))
