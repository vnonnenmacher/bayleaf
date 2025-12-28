import uuid

from django.contrib.auth import get_user_model
from django.db import models

from core.models import Service, TimeStampedModel
from patients.models import Patient
from professionals.models import Professional


class SampleState(models.Model):
    """
    Represents a state in the sample's lifecycle (e.g., Collected, Transported, Stored).
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_initial_state = models.BooleanField(default=False)  # True if this is the initial state
    is_final_state = models.BooleanField(default=False)  # True if this is the final state

    def __str__(self):
        return self.name


class AllowedStateTransition(models.Model):
    """
    Represents a valid state transition for a sample.
    """
    from_state = models.ForeignKey(SampleState, on_delete=models.CASCADE, related_name="allowed_transitions")
    to_state = models.ForeignKey(SampleState, on_delete=models.CASCADE, related_name="incoming_transitions")


class SampleType(models.Model):
    """
    Represents the type of biological sample (e.g., Blood, Tissue, Urine).
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Sample(models.Model):
    """
    Represents a biological sample collected from a patient.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="samples")
    sample_type = models.ForeignKey(SampleType, on_delete=models.CASCADE, related_name="samples")
    exam_request = models.ForeignKey(
        "ExamRequest",
        on_delete=models.SET_NULL,
        related_name="samples",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Sample {self.id} - {self.sample_type.name}"

    def get_current_state(self):
        """Retrieves the latest verified state transition."""
        latest_transition = self.state_transitions.filter(is_verified=True).order_by('-created_at').first()
        return latest_transition.new_state if latest_transition else None


class SampleStateTransition(models.Model):
    """
    Tracks state transitions for a sample and links them to blockchain records.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="state_transitions")
    previous_state = models.ForeignKey(SampleState, on_delete=models.SET_NULL, null=True, related_name="previous_transitions")
    new_state = models.ForeignKey(SampleState, on_delete=models.CASCADE, related_name="new_transitions")
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(blank=True, null=True)  # Timestamp when the transition was validated

    # Blockchain validation
    is_valid = models.BooleanField(default=None, null=True)  # Null until blockchain validation happens
    validation_message = models.TextField(blank=True, null=True)  # Reason for rejection, if any

    # Blockchain record
    transaction_hash = models.CharField(max_length=128, unique=True, blank=True, null=True)  # Blockchain transaction hash
    blockchain_timestamp = models.DateTimeField(blank=True, null=True)  # Timestamp of blockchain transaction
    is_verified = models.BooleanField(default=False)  # True when transaction is confirmed on-chain

    metadata = models.JSONField(blank=True, null=True)  # Extra metadata

    def __str__(self):
        return f"Sample {self.sample.id}: {self.previous_state} → {self.new_state} at {self.created_at}"


class MeasurementUnit(models.Model):
    """
    Represents a unit of measurement for exam fields (e.g., mg/dL).
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.code


class Exam(Service):
    """
    Represents a lab exam as a service (e.g., Glucose).
    """
    material = models.ForeignKey(SampleType, on_delete=models.PROTECT, related_name="exams")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class ExamVersion(TimeStampedModel):
    """
    Versioned definition of an exam; only one version is active at a time.
    """
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("exam", "version")

    def __str__(self):
        return f"{self.exam.code} v{self.version}"


class ExamField(TimeStampedModel):
    """
    Defines a field for an exam version (e.g., Result, Observation).
    """

    class FieldType(models.TextChoices):
        NUMBER = "number", "Number"
        TEXT = "text", "Text"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        DATETIME = "datetime", "DateTime"
        DECIMAL = "decimal", "Decimal"

    exam_version = models.ForeignKey(ExamVersion, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=64, blank=True, null=True)
    priority = models.PositiveIntegerField(default=0)
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    measurement_unit = models.ForeignKey(
        MeasurementUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exam_fields",
    )
    formula = models.JSONField(blank=True, null=True)
    classification_rules = models.JSONField(blank=True, null=True)
    is_required = models.BooleanField(default=False)

    class Meta:
        unique_together = ("exam_version", "code")

    def __str__(self):
        return f"{self.exam_version} - {self.name}"


class Tag(TimeStampedModel):
    """
    Tag definition that can be attached to exam fields when formula evaluates to true.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    formula = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name


class ExamFieldTag(models.Model):
    exam_field = models.ForeignKey(ExamField, on_delete=models.CASCADE, related_name="tag_links")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="field_links")

    class Meta:
        unique_together = ("exam_field", "tag")


class ExamRequest(TimeStampedModel):
    """
    A request for a set of exams made by a professional.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="exam_requests")
    requested_by = models.ForeignKey(Professional, on_delete=models.PROTECT, related_name="exam_requests")
    notes = models.TextField(blank=True, null=True)
    canceled_at = models.DateTimeField(blank=True, null=True)
    canceled_by = models.ForeignKey(
        Professional,
        on_delete=models.SET_NULL,
        related_name="canceled_exam_requests",
        blank=True,
        null=True,
    )
    cancel_reason = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Exam request {self.id} for {self.patient}"


class RequestedExam(TimeStampedModel):
    """
    A requested exam within an exam request.
    """
    exam_request = models.ForeignKey(ExamRequest, on_delete=models.CASCADE, related_name="requested_exams")
    exam_version = models.ForeignKey(ExamVersion, on_delete=models.PROTECT, related_name="requested_exams")
    sample = models.ForeignKey(Sample, on_delete=models.SET_NULL, related_name="requested_exams", null=True, blank=True)

    class Meta:
        unique_together = ("exam_request", "exam_version")

    def __str__(self):
        return f"{self.exam_request} - {self.exam_version}"


class ExamFieldResult(TimeStampedModel):
    """
    Result for a specific exam field within a requested exam.
    """

    class Classification(models.TextChoices):
        NORMAL = "normal", "Normal"
        ABNORMAL = "abnormal", "Abnormal"
        CRITICAL = "critical", "Critical"

    requested_exam = models.ForeignKey(RequestedExam, on_delete=models.CASCADE, related_name="field_results")
    exam_field = models.ForeignKey(ExamField, on_delete=models.PROTECT, related_name="field_results")
    raw_value = models.TextField(blank=True, null=True)
    computed_value = models.TextField(blank=True, null=True)
    classification = models.CharField(
        max_length=20,
        choices=Classification.choices,
        blank=True,
        null=True,
    )
    classification_context = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ("requested_exam", "exam_field")

    def __str__(self):
        return f"{self.requested_exam} - {self.exam_field.name}"


class ExamFieldResultTag(models.Model):
    exam_field_result = models.ForeignKey(
        ExamFieldResult,
        on_delete=models.CASCADE,
        related_name="applied_tags",
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="result_links")
    rule_matched = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ("exam_field_result", "tag")

    def __str__(self):
        return f"{self.exam_field_result} - {self.tag.name}"


class EquipmentGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    group = models.ForeignKey(EquipmentGroup, on_delete=models.CASCADE, related_name="equipments")
    manufacturer = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Analyte(models.Model):
    """
    Represents a measurable analyte from equipment (e.g., RBC).
    """
    name = models.CharField(max_length=100, unique=True)
    group = models.ForeignKey(EquipmentGroup, on_delete=models.CASCADE, related_name="analytes")
    default_code = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class AnalyteCode(models.Model):
    """
    Equipment-specific code for an analyte.
    """
    analyte = models.ForeignKey(Analyte, on_delete=models.CASCADE, related_name="codes")
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name="analyte_codes")
    code = models.CharField(max_length=50)
    is_default = models.BooleanField(default=False)
    configuration = models.JSONField(blank=True, null=True)

    class Meta:
        unique_together = ("analyte", "equipment")

    def __str__(self):
        return f"{self.analyte.name} - {self.code} ({self.equipment.name})"


class AnalyteResult(TimeStampedModel):
    """
    Result received from equipment for a sample/analyte.
    """
    analyte = models.ForeignKey(Analyte, on_delete=models.PROTECT, related_name="results")
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="results")
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="analyte_results")
    requested_exam = models.ForeignKey(
        RequestedExam,
        on_delete=models.SET_NULL,
        related_name="analyte_results",
        null=True,
        blank=True,
    )
    raw_value = models.TextField()
    numeric_value = models.FloatField(blank=True, null=True)
    units = models.ForeignKey(MeasurementUnit, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.analyte.name} result for {self.sample.id}"
