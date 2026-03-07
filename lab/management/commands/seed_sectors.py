from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from lab.models import Sector


SECTOR_CATALOG = {
    "pt": [
        {
            "name": "Bioquimica",
            "description": "Setor para analises bioquimicas, enzimas, glicose e perfil metabolico.",
        },
        {
            "name": "Imunologia",
            "description": "Setor para exames imunologicos, sorologias e marcadores de resposta imune.",
        },
        {
            "name": "Microbiologia",
            "description": "Setor para culturas, identificacao microbiana e testes de sensibilidade.",
        },
        {
            "name": "Parasitologia",
            "description": "Setor para pesquisa e identificacao de parasitas em amostras clinicas.",
        },
        {
            "name": "Hematologia",
            "description": "Setor para hemograma, coagulacao e estudos hematologicos.",
        },
        {
            "name": "Urinanalise",
            "description": "Setor para exames de urina, sedimentoscopia e testes fisico-quimicos.",
        },
    ],
    "en": [
        {
            "name": "Biochemistry",
            "description": "Section for biochemical tests, enzymes, glucose, and metabolic profiles.",
        },
        {
            "name": "Immunology",
            "description": "Section for immunology panels, serology, and immune response markers.",
        },
        {
            "name": "Microbiology",
            "description": "Section for culture, microbial identification, and susceptibility testing.",
        },
        {
            "name": "Parasitology",
            "description": "Section for detection and identification of parasites in clinical samples.",
        },
        {
            "name": "Hematology",
            "description": "Section for complete blood count, coagulation, and hematology studies.",
        },
        {
            "name": "Urinalysis",
            "description": "Section for urine exams, sediment microscopy, and chemistry testing.",
        },
    ],
}


class Command(BaseCommand):
    help = "Seed default lab sectors in Portuguese or English."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lang",
            default="pt",
            choices=("pt", "en"),
            help="Language for seeded sector names and descriptions.",
        )

    def handle(self, *args, **options):
        lang = options["lang"]
        catalog = SECTOR_CATALOG.get(lang)
        if not catalog:
            raise CommandError(f"Unsupported language: {lang}")

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in catalog:
                sector, created = Sector.objects.get_or_create(
                    name=entry["name"],
                    defaults={"description": entry["description"]},
                )
                if created:
                    created_count += 1
                    continue

                if sector.description != entry["description"]:
                    sector.description = entry["description"]
                    sector.save(update_fields=["description"])
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sectors seeded for '{lang}'. Created: {created_count}. Updated: {updated_count}."
            )
        )
