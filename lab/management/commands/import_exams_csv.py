import csv
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from lab.models import Exam, ExamField, ExamFieldTag, ExamVersion, MeasurementUnit, SampleType, Tag


def _parse_bool(value, default=False):
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_json(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc


class Command(BaseCommand):
    help = "Import exams, versions, and fields from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and validate, but do not write to the database.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        dry_run = options["dry_run"]

        with open(csv_path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise CommandError("CSV file has no headers.")

            required = {
                "exam_code",
                "exam_name",
                "exam_material",
                "exam_version",
                "field_name",
                "field_type",
            }
            missing = required - set(reader.fieldnames)
            if missing:
                raise CommandError(f"Missing required columns: {sorted(missing)}")

            with transaction.atomic():
                for idx, row in enumerate(reader, start=2):
                    try:
                        self._import_row(row)
                    except Exception as exc:
                        raise CommandError(f"Row {idx}: {exc}") from exc

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.WARNING("Dry-run complete; no changes saved."))
                else:
                    self.stdout.write(self.style.SUCCESS("Import completed."))

    def _import_row(self, row):
        exam_code = str(row.get("exam_code", "")).strip()
        exam_name = str(row.get("exam_name", "")).strip()
        exam_description = str(row.get("exam_description", "")).strip() or None
        exam_material = str(row.get("exam_material", "")).strip()
        exam_is_active = _parse_bool(row.get("exam_is_active"), default=True)

        if not exam_code or not exam_name or not exam_material:
            raise ValueError("exam_code, exam_name, and exam_material are required.")

        sample_type, _ = SampleType.objects.get_or_create(name=exam_material)

        exam, created = Exam.objects.get_or_create(
            code=exam_code,
            defaults={
                "name": exam_name,
                "description": exam_description,
                "material": sample_type,
                "is_active": exam_is_active,
            },
        )
        if not created:
            exam.name = exam_name
            exam.description = exam_description
            exam.material = sample_type
            exam.is_active = exam_is_active
            exam.save(update_fields=["name", "description", "material", "is_active"])

        version_number = _parse_int(row.get("exam_version"))
        version_notes = str(row.get("exam_version_notes", "")).strip() or None
        version_is_active = _parse_bool(row.get("exam_version_is_active"), default=False)

        if version_number <= 0:
            raise ValueError("exam_version must be a positive integer.")

        if version_is_active:
            ExamVersion.objects.filter(exam=exam, is_active=True).update(is_active=False)

        exam_version, created = ExamVersion.objects.get_or_create(
            exam=exam,
            version=version_number,
            defaults={"notes": version_notes, "is_active": version_is_active},
        )
        if not created:
            exam_version.notes = version_notes
            exam_version.is_active = version_is_active
            exam_version.save(update_fields=["notes", "is_active"])

        field_name = str(row.get("field_name", "")).strip()
        field_code = str(row.get("field_code", "")).strip() or None
        field_priority = _parse_int(row.get("field_priority"), default=0)
        field_type = str(row.get("field_type", "")).strip() or ExamField.FieldType.TEXT
        field_is_required = _parse_bool(row.get("field_is_required"), default=False)
        measurement_unit_code = str(row.get("field_measurement_unit_code", "")).strip()
        measurement_unit_name = str(row.get("field_measurement_unit_name", "")).strip()
        field_formula = _parse_json(row.get("field_formula"))
        field_classification_rules = _parse_json(row.get("field_classification_rules"))

        if not field_name:
            raise ValueError("field_name is required.")

        measurement_unit = None
        if measurement_unit_code:
            measurement_unit, _ = MeasurementUnit.objects.get_or_create(
                code=measurement_unit_code,
                defaults={"name": measurement_unit_name or measurement_unit_code},
            )
            if measurement_unit_name:
                measurement_unit.name = measurement_unit_name
                measurement_unit.save(update_fields=["name"])

        if field_code:
            field, created = ExamField.objects.get_or_create(
                exam_version=exam_version,
                code=field_code,
                defaults={
                    "name": field_name,
                    "priority": field_priority,
                    "field_type": field_type,
                    "measurement_unit": measurement_unit,
                    "formula": field_formula,
                    "classification_rules": field_classification_rules,
                    "is_required": field_is_required,
                },
            )
        else:
            field, created = ExamField.objects.get_or_create(
                exam_version=exam_version,
                name=field_name,
                defaults={
                    "code": None,
                    "priority": field_priority,
                    "field_type": field_type,
                    "measurement_unit": measurement_unit,
                    "formula": field_formula,
                    "classification_rules": field_classification_rules,
                    "is_required": field_is_required,
                },
            )

        if not created:
            field.name = field_name
            field.priority = field_priority
            field.field_type = field_type
            field.measurement_unit = measurement_unit
            field.formula = field_formula
            field.classification_rules = field_classification_rules
            field.is_required = field_is_required
            field.save(
                update_fields=[
                    "name",
                    "priority",
                    "field_type",
                    "measurement_unit",
                    "formula",
                    "classification_rules",
                    "is_required",
                ]
            )

        tag_names = str(row.get("field_tags", "")).strip()
        tag_descriptions = _parse_json(row.get("tag_descriptions_json"))
        tag_formulas = _parse_json(row.get("tag_formulas_json"))

        if tag_names:
            names = [t.strip() for t in tag_names.split(",") if t.strip()]
            for name in names:
                tag, _ = Tag.objects.get_or_create(name=name)
                if isinstance(tag_descriptions, dict) and name in tag_descriptions:
                    tag.description = tag_descriptions[name]
                if isinstance(tag_formulas, dict) and name in tag_formulas:
                    tag.formula = tag_formulas[name]
                if tag.description is not None or tag.formula is not None:
                    tag.save(update_fields=["description", "formula"])
                ExamFieldTag.objects.get_or_create(exam_field=field, tag=tag)
