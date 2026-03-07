from django.core.management.base import BaseCommand
from django.db import transaction

from lab.models import Equipment, EquipmentGroup


ANALYZERS = [
    {
        "code": "WEB_ROCHE_COBAS_8000",
        "name": "cobas 8000 modular analyzer series",
        "manufacturer": "Roche Diagnostics",
        "group": "Integrated Chemistry & Immunoassay",
    },
    {
        "code": "WEB_ROCHE_COBAS_E411",
        "name": "cobas e 411 analyzer",
        "manufacturer": "Roche Diagnostics",
        "group": "Immunology",
    },
    {
        "code": "WEB_ABBOTT_ALINITY_C",
        "name": "Alinity c",
        "manufacturer": "Abbott",
        "group": "Clinical Chemistry",
    },
    {
        "code": "WEB_ABBOTT_ALINITY_I",
        "name": "Alinity i",
        "manufacturer": "Abbott",
        "group": "Immunology",
    },
    {
        "code": "WEB_SIEMENS_ATELLICA_CH930",
        "name": "Atellica CH 930 Analyzer",
        "manufacturer": "Siemens Healthineers",
        "group": "Clinical Chemistry",
    },
    {
        "code": "WEB_BECKMAN_AU5800",
        "name": "AU5800 Series Clinical Chemistry Analyzers",
        "manufacturer": "Beckman Coulter",
        "group": "Clinical Chemistry",
    },
    {
        "code": "WEB_BECKMAN_DXH900",
        "name": "DxH 900",
        "manufacturer": "Beckman Coulter",
        "group": "Hematology",
    },
    {
        "code": "WEB_SYSMEX_XN1000",
        "name": "XN-1000 Automated Hematology Analyzer",
        "manufacturer": "Sysmex",
        "group": "Hematology",
    },
    {
        "code": "WEB_SYSMEX_CS2500",
        "name": "Sysmex CS-2500 Automated Blood Coagulation Analyzer",
        "manufacturer": "Sysmex",
        "group": "Coagulation",
    },
    {
        "code": "WEB_BIOMERIEUX_VIDAS3",
        "name": "VIDAS 3",
        "manufacturer": "bioMerieux",
        "group": "Immunology",
    },
]


class Command(BaseCommand):
    help = "Seed lab analyzers curated from manufacturer product pages."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        with transaction.atomic():
            for entry in ANALYZERS:
                group, _ = EquipmentGroup.objects.get_or_create(name=entry["group"])

                equipment = Equipment.objects.filter(code=entry["code"]).first()
                if equipment is None:
                    equipment = Equipment.objects.filter(name=entry["name"]).first()

                if equipment is None:
                    Equipment.objects.create(
                        code=entry["code"],
                        name=entry["name"],
                        group=group,
                        manufacturer=entry["manufacturer"],
                    )
                    created += 1
                    continue

                has_changes = False
                if equipment.name != entry["name"]:
                    equipment.name = entry["name"]
                    has_changes = True
                if equipment.group_id != group.id:
                    equipment.group = group
                    has_changes = True
                if equipment.manufacturer != entry["manufacturer"]:
                    equipment.manufacturer = entry["manufacturer"]
                    has_changes = True
                if equipment.code != entry["code"]:
                    equipment.code = entry["code"]
                    has_changes = True

                if has_changes:
                    equipment.save()
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded web lab analyzers. Created: {created}. Updated: {updated}. Total listed: {len(ANALYZERS)}."
            )
        )
