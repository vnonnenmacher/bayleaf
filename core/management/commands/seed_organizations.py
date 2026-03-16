import random

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Organization
from professionals.models import Professional


ORGANIZATIONS = [
    ("Unimed Serra Gaucha", "UNIMED_SERRA_GAUCHA"),
    ("Hospital Pompeia", "HOSPITAL_POMPEIA"),
    ("Unimed Porto Alegre", "UNIMED_PORTO_ALEGRE"),
]


class Command(BaseCommand):
    help = (
        "Creates default organizations and assigns each existing professional "
        "to one random organization."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        organizations = []
        for name, code in ORGANIZATIONS:
            org, created = Organization.objects.get_or_create(
                code=code,
                defaults={"name": name, "is_active": True},
            )
            if not created and org.name != name:
                org.name = name
                org.save(update_fields=["name", "updated_at"])
            organizations.append(org)

        organization_ids = [org.id for org in organizations]
        professionals = Professional.objects.all()

        for professional in professionals:
            selected_org = random.choice(organizations)
            professional.organizations.remove(
                *professional.organizations.filter(id__in=organization_ids)
            )
            professional.organizations.add(selected_org)

        self.stdout.write(
            self.style.SUCCESS(
                f"Organizations ready ({len(organizations)}). "
                f"Assigned {professionals.count()} professionals."
            )
        )
