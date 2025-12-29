import json
from pathlib import Path

import pytest

from lab.exam_processing.processor import ExamProcessor
from lab.exam_processing.validator import ExamFormulaValidator
from lab.models import (
    Analyte,
    AnalyteCode,
    AnalyteResult,
    Equipment,
    EquipmentGroup,
    ExamField,
    ExamFieldResult,
    MeasurementUnit,
    RequestedExam,
)


@pytest.fixture
def formula_samples_dir():
    return Path(__file__).parent / "formula_samples"


@pytest.fixture
def equipment_group(db):
    return EquipmentGroup.objects.create(name="Chemistry")


@pytest.fixture
def equipment(db, equipment_group):
    return Equipment.objects.create(name="Analyzer", group=equipment_group)


@pytest.fixture
def analyte(db, equipment_group):
    return Analyte.objects.create(name="Glucose", group=equipment_group, default_code="GLU")


@pytest.fixture
def analyte_code(db, analyte, equipment):
    return AnalyteCode.objects.create(analyte=analyte, equipment=equipment, code="GLU-1")


@pytest.fixture
def measurement_unit(db):
    return MeasurementUnit.objects.create(name="Milligrams per deciliter", code="mg/dL")


@pytest.fixture
def requested_exam(db, exam_request, exam_version, sample):
    sample.exam_request = exam_request
    sample.save(update_fields=["exam_request"])
    return RequestedExam.objects.create(
        exam_request=exam_request,
        exam_version=exam_version,
        sample=sample,
    )


@pytest.mark.django_db
def test_validator_accepts_valid_formulas(formula_samples_dir):
    validator = ExamFormulaValidator()
    for name in ["valid_simple.json", "valid_conditional.json"]:
        data = json.loads((formula_samples_dir / name).read_text())
        assert validator.is_valid(data)


@pytest.mark.django_db
def test_validator_rejects_invalid_formulas(formula_samples_dir):
    validator = ExamFormulaValidator()
    invalid_files = [
        "invalid_not_list.json",
        "invalid_syntax.json",
        "invalid_reference_field.json",
        "invalid_rule_shape.json",
        "invalid_result_type.json",
    ]
    for name in invalid_files:
        data = json.loads((formula_samples_dir / name).read_text())
        errors = validator.validate(data)
        assert errors


@pytest.mark.django_db
def test_processor_creates_result_from_analyte(
    requested_exam,
    analyte_code,
    analyte,
    equipment,
    measurement_unit,
):
    AnalyteResult.objects.create(
        analyte=analyte,
        equipment=equipment,
        sample=requested_exam.sample,
        requested_exam=requested_exam,
        raw_value="5.5",
        numeric_value=5.5,
        units=measurement_unit,
    )
    exam_field = ExamField.objects.create(
        exam_version=requested_exam.exam_version,
        name="Glucose Value",
        code="GLU_VAL",
        formula=[
            {
                "condition": "",
                "result": f"analyte_code_result({analyte_code.id}).numeric_value",
            }
        ],
    )

    ExamProcessor()._compute_requested_exam(requested_exam)

    result = ExamFieldResult.objects.filter(
        requested_exam=requested_exam,
        exam_field=exam_field,
    ).first()
    assert result is not None
    assert result.computed_value == "5.5"


@pytest.mark.django_db
def test_processor_skips_when_reference_missing(requested_exam, analyte_code):
    exam_field = ExamField.objects.create(
        exam_version=requested_exam.exam_version,
        name="Missing Value",
        code="MISS_VAL",
        formula=[
            {
                "condition": "",
                "result": f"analyte_code_result({analyte_code.id}).numeric_value",
            }
        ],
    )

    ExamProcessor()._compute_requested_exam(requested_exam)

    assert not ExamFieldResult.objects.filter(
        requested_exam=requested_exam,
        exam_field=exam_field,
    ).exists()


@pytest.mark.django_db
def test_processor_orders_field_dependencies(
    requested_exam,
    analyte_code,
    analyte,
    equipment,
):
    AnalyteResult.objects.create(
        analyte=analyte,
        equipment=equipment,
        sample=requested_exam.sample,
        requested_exam=requested_exam,
        raw_value="2",
        numeric_value=2,
    )
    field_one = ExamField.objects.create(
        exam_version=requested_exam.exam_version,
        name="Base",
        code="BASE",
        formula=[
            {
                "condition": "",
                "result": f"analyte_code_result({analyte_code.id}).numeric_value",
            }
        ],
    )
    field_two = ExamField.objects.create(
        exam_version=requested_exam.exam_version,
        name="Derived",
        code="DERIVED",
        formula=[
            {
                "condition": "",
                "result": f"exam_field_result({field_one.id}).numeric_value * 2",
            }
        ],
    )

    ExamProcessor()._compute_requested_exam(requested_exam)

    result = ExamFieldResult.objects.filter(
        requested_exam=requested_exam,
        exam_field=field_two,
    ).first()
    assert result is not None
    assert result.computed_value == "4.0"
