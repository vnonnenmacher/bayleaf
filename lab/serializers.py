from rest_framework import serializers

from lab.helpers.exam_request_helper import ExamRequestHelper
from lab.models import (
    AllowedStateTransition,
    Analyte,
    AnalyteCode,
    AnalyteResult,
    Exam,
    ExamField,
    ExamFieldResult,
    ExamFieldTag,
    ExamRequest,
    ExamVersion,
    Equipment,
    EquipmentGroup,
    MeasurementUnit,
    RequestedExam,
    Sample,
    SampleState,
    SampleType,
    Tag,
)
from patients.models import Patient
from patients.serializers import ReducedPatientSerializer
from professionals.models import Professional


# Serializers
class SampleSerializer(serializers.ModelSerializer):
    patient_uuid = serializers.UUIDField(write_only=True)
    current_state = serializers.SerializerMethodField(read_only=True)
    patient = ReducedPatientSerializer(read_only=True)

    class Meta:
        model = Sample
        fields = ['id', 'patient_uuid', 'sample_type', 'current_state', 'patient']

    def validate_patient_uuid(self, value):
        if not Patient.objects.filter(pid=value).exists():
            raise serializers.ValidationError("Patient not found.")
        return value

    def create(self, validated_data):
        patient = Patient.objects.get(pid=validated_data.pop('patient_uuid'))
        sample = Sample.objects.create(patient=patient, **validated_data)
        return sample

    def get_current_state(self, obj):
        state = obj.get_current_state()
        if state:
            return {
                "id": state.id,
                "name": state.name
            }
        return None


class SampleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleType
        fields = ['id', 'name', 'description', 'created_at']


class SampleStateSerializer(serializers.ModelSerializer):
    # 🔸 Accept list of state IDs on write
    allowed_transitions = serializers.PrimaryKeyRelatedField(
        queryset=SampleState.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    incoming_transitions = serializers.PrimaryKeyRelatedField(
        queryset=SampleState.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    # 🔸 Return full state objects (id + name) on read
    allowed_transitions_detail = serializers.SerializerMethodField()
    incoming_transitions_detail = serializers.SerializerMethodField()

    class Meta:
        model = SampleState
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "is_initial_state",
            "is_final_state",
            "allowed_transitions",
            "incoming_transitions",
            "allowed_transitions_detail",
            "incoming_transitions_detail",
        ]
        read_only_fields = ("created_at",)

    # 🔸 GET method: output full objects for allowed transitions
    def get_allowed_transitions_detail(self, obj):
        return [
            {"id": t.to_state.id, "name": t.to_state.name}
            for t in obj.allowed_transitions.select_related("to_state").all()
        ]

    # 🔸 GET method: output full objects for incoming transitions
    def get_incoming_transitions_detail(self, obj):
        return [
            {"id": t.from_state.id, "name": t.from_state.name}
            for t in obj.incoming_transitions.select_related("from_state").all()
        ]

    def create(self, validated_data):
        allowed_transitions = validated_data.pop("allowed_transitions", [])
        incoming_transitions = validated_data.pop("incoming_transitions", [])

        sample_state = SampleState.objects.create(**validated_data)

        for to_state in allowed_transitions:
            AllowedStateTransition.objects.create(from_state=sample_state, to_state=to_state)

        for from_state in incoming_transitions:
            AllowedStateTransition.objects.create(from_state=from_state, to_state=sample_state)

        return sample_state

    def update(self, instance, validated_data):
        allowed_transitions = validated_data.pop("allowed_transitions", [])
        incoming_transitions = validated_data.pop("incoming_transitions", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if allowed_transitions:
            AllowedStateTransition.objects.filter(from_state=instance).delete()
            for to_state in allowed_transitions:
                AllowedStateTransition.objects.create(from_state=instance, to_state=to_state)

        if incoming_transitions:
            AllowedStateTransition.objects.filter(to_state=instance).delete()
            for from_state in incoming_transitions:
                AllowedStateTransition.objects.create(from_state=from_state, to_state=instance)

        return instance


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ["id", "name", "code", "description"]


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ["id", "name", "code", "description", "material", "is_active"]


class ExamVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamVersion
        fields = ["id", "exam", "version", "is_active", "notes", "created_at", "updated_at"]
        read_only_fields = ("created_at", "updated_at")

    def _ensure_single_active(self, exam):
        ExamVersion.objects.filter(exam=exam, is_active=True).update(is_active=False)

    def create(self, validated_data):
        is_active = validated_data.get("is_active", False)
        exam = validated_data["exam"]
        if is_active:
            self._ensure_single_active(exam)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        is_active = validated_data.get("is_active", instance.is_active)
        if is_active:
            self._ensure_single_active(instance.exam)
        return super().update(instance, validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "description", "formula", "created_at", "updated_at"]
        read_only_fields = ("created_at", "updated_at")


class ExamFieldSerializer(serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )
    tags = serializers.SerializerMethodField()

    class Meta:
        model = ExamField
        fields = [
            "id",
            "exam_version",
            "name",
            "code",
            "priority",
            "field_type",
            "measurement_unit",
            "formula",
            "classification_rules",
            "is_required",
            "tag_ids",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tags = validated_data.pop("tag_ids", [])
        exam_field = super().create(validated_data)
        for tag in tags:
            ExamFieldTag.objects.get_or_create(exam_field=exam_field, tag=tag)
        return exam_field

    def update(self, instance, validated_data):
        tags = validated_data.pop("tag_ids", None)
        exam_field = super().update(instance, validated_data)
        if tags is not None:
            ExamFieldTag.objects.filter(exam_field=exam_field).delete()
            for tag in tags:
                ExamFieldTag.objects.get_or_create(exam_field=exam_field, tag=tag)
        return exam_field

    def get_tags(self, obj):
        tags = Tag.objects.filter(field_links__exam_field=obj)
        return TagSerializer(tags, many=True).data


class RequestedExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestedExam
        fields = ["id", "exam_version", "sample", "created_at", "updated_at"]
        read_only_fields = ("created_at", "updated_at")


class ExamRequestSerializer(serializers.ModelSerializer):
    patient_uuid = serializers.UUIDField(write_only=True)
    exam_version_ids = serializers.PrimaryKeyRelatedField(
        queryset=ExamVersion.objects.all(),
        many=True,
        write_only=True,
    )
    requested_exams = RequestedExamSerializer(read_only=True, many=True)
    samples = SampleSerializer(read_only=True, many=True)
    canceled_by = serializers.PrimaryKeyRelatedField(read_only=True)
    canceled_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ExamRequest
        fields = [
            "id",
            "patient_uuid",
            "notes",
            "exam_version_ids",
            "requested_exams",
            "samples",
            "canceled_at",
            "canceled_by",
            "cancel_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at", "canceled_at", "canceled_by", "cancel_reason")

    def validate_patient_uuid(self, value):
        if not Patient.objects.filter(pid=value).exists():
            raise serializers.ValidationError("Patient not found.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        patient = Patient.objects.get(pid=validated_data.pop("patient_uuid"))
        exam_versions = validated_data.pop("exam_version_ids")
        professional = Professional.objects.get(id=request.user.id)

        helper = ExamRequestHelper()
        return helper.create_exam_request(
            patient=patient,
            requested_by=professional,
            exam_versions=exam_versions,
            **validated_data,
        )


class ExamRequestCancelSerializer(serializers.Serializer):
    cancel_reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class ExamFieldResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamFieldResult
        fields = [
            "id",
            "requested_exam",
            "exam_field",
            "raw_value",
            "computed_value",
            "classification",
            "classification_context",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")


class EquipmentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentGroup
        fields = ["id", "name", "description"]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ["id", "name", "group", "manufacturer"]


class AnalyteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analyte
        fields = ["id", "name", "group", "default_code"]


class AnalyteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyteCode
        fields = ["id", "analyte", "equipment", "code", "is_default", "configuration"]


class AnalyteResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyteResult
        fields = [
            "id",
            "analyte",
            "equipment",
            "sample",
            "requested_exam",
            "raw_value",
            "numeric_value",
            "units",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")
