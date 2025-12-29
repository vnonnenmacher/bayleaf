import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from lab.models import Analyte, Equipment, EquipmentGroup


class Command(BaseCommand):
    help = "Seed equipment groups, equipment, and analytes from the equipment catalog."

    def handle(self, *args, **options):
        catalog = self._load_catalog()
        groups = catalog.get("groups")
        if not isinstance(groups, list):
            raise CommandError("Catalog must contain a 'groups' list.")

        with transaction.atomic():
            for group_data in groups:
                self._seed_group(group_data)

        self.stdout.write(self.style.SUCCESS("Equipment catalog seeded."))

    def _load_catalog(self) -> dict:
        catalog_path = Path(__file__).resolve().parent / "data" / "equipment_catalog.json"
        try:
            with catalog_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            raise CommandError(f"Catalog file not found: {catalog_path}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Catalog JSON invalid: {exc}") from exc

    def _seed_group(self, group_data: dict) -> None:
        if not isinstance(group_data, dict):
            raise CommandError("Group entry must be an object.")
        name = str(group_data.get("name", "")).strip()
        if not name:
            raise CommandError("Group entry missing name.")

        description = str(group_data.get("description", "")).strip() or None
        group, created = EquipmentGroup.objects.get_or_create(
            name=name,
            defaults={"description": description},
        )
        if not created and group.description != description:
            group.description = description
            group.save(update_fields=["description"])

        for equipment in group_data.get("equipments", []) or []:
            self._upsert_equipment(group, equipment)
        for analyte in group_data.get("analytes", []) or []:
            self._upsert_analyte(group, analyte)

    def _upsert_equipment(self, group: EquipmentGroup, equipment_data: dict) -> None:
        if not isinstance(equipment_data, dict):
            raise CommandError("Equipment entry must be an object.")
        code = str(equipment_data.get("code", "")).strip()
        name = str(equipment_data.get("name", "")).strip()
        manufacturer = str(equipment_data.get("manufacturer", "")).strip() or None
        if not code or not name:
            raise CommandError("Equipment entries require 'code' and 'name'.")

        equipment = Equipment.objects.filter(code=code).first()
        if equipment is None:
            equipment = Equipment.objects.filter(name=name).first()
        if equipment is None:
            Equipment.objects.create(
                code=code,
                name=name,
                group=group,
                manufacturer=manufacturer,
            )
            return

        updates = {}
        if equipment.code != code:
            updates["code"] = code
        if equipment.name != name:
            updates["name"] = name
        if equipment.group_id != group.id:
            updates["group"] = group
        if equipment.manufacturer != manufacturer:
            updates["manufacturer"] = manufacturer
        if updates:
            for key, value in updates.items():
                setattr(equipment, key, value)
            equipment.save(update_fields=list(updates.keys()))

    def _upsert_analyte(self, group: EquipmentGroup, analyte_data: dict) -> None:
        if not isinstance(analyte_data, dict):
            raise CommandError("Analyte entry must be an object.")
        code = str(analyte_data.get("code", "")).strip()
        name = str(analyte_data.get("name", "")).strip()
        if not code or not name:
            raise CommandError("Analyte entries require 'code' and 'name'.")

        analyte, created = Analyte.objects.get_or_create(
            name=name,
            defaults={"group": group, "default_code": code},
        )
        updates = {}
        if not created:
            if analyte.group_id != group.id:
                updates["group"] = group
            if analyte.default_code != code:
                updates["default_code"] = code
        if updates:
            for key, value in updates.items():
                setattr(analyte, key, value)
            analyte.save(update_fields=list(updates.keys()))
