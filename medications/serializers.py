from rest_framework import serializers
from patients.models import Patient
from professionals.models import Professional
from core.models import DosageUnit
from core.serializers import DosageUnitSerializer
from .models import Medication, MedicationItem, MedicationPrescription


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "name", "description"]


class MedicationPrescribeSerializer(serializers.Serializer):
    patient_uuid = serializers.UUIDField()
    medication = serializers.PrimaryKeyRelatedField(queryset=Medication.objects.all())
    dosage_unit = serializers.CharField()
    dosage_amount = serializers.DecimalField(max_digits=6, decimal_places=2)
    frequency_hours = serializers.IntegerField()
    total_unit_amount = serializers.IntegerField(min_value=1)

    def validate(self, data):
        # Validate patient
        try:
            data["patient"] = Patient.objects.get(pid=data["patient_uuid"])
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found.")

        # Validate dosage unit
        try:
            data["dosage_unit_obj"] = DosageUnit.objects.get(code__iexact=data["dosage_unit"])
        except DosageUnit.DoesNotExist:
            raise serializers.ValidationError("Invalid dosage unit.")

        return data

    def create(self, validated_data):
        patient = validated_data["patient"]
        professional = self.context["request"].user
        dosage_unit = validated_data["dosage_unit_obj"]

        prescription = MedicationPrescription.objects.create(
            professional=Professional.objects.get(user_ptr_id=professional.id),
            patient=patient
        )

        MedicationItem.objects.create(
            prescription=prescription,
            medication=validated_data["medication"],
            dosage_amount=validated_data["dosage_amount"],
            dosage_unit=dosage_unit,
            frequency_hours=validated_data["frequency_hours"],
            total_unit_amount=validated_data["total_unit_amount"],
        )

        return prescription


class MedicationItemSerializer(serializers.ModelSerializer):
    medication = MedicationSerializer(read_only=True)
    dosage_unit = DosageUnitSerializer(read_only=True)

    class Meta:
        model = MedicationItem
        fields = (
            "id",
            "medication",
            "dosage_amount",
            "dosage_unit",
            "frequency_hours",
            "instructions",
            "total_unit_amount",
        )


class MedicationItemCreateSerializer(serializers.Serializer):
    medication = serializers.PrimaryKeyRelatedField(queryset=Medication.objects.all())
    dosage_unit = serializers.CharField()
    dosage_amount = serializers.DecimalField(max_digits=6, decimal_places=2)
    frequency_hours = serializers.IntegerField(min_value=1)
    total_unit_amount = serializers.IntegerField(min_value=1)
    instructions = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        # Validate dosage unit by code (case-insensitive)
        try:
            du = DosageUnit.objects.get(code__iexact=data["dosage_unit"])
        except DosageUnit.DoesNotExist:
            raise serializers.ValidationError("Invalid dosage unit.")

        data["dosage_unit_obj"] = du
        return data

    def create(self, validated_data):
        return MedicationItem.objects.create(
            prescription=None,  # standalone item (no prescription)
            patient=Patient.objects.get(user_ptr_id=self.context["request"].user.id),
            medication=validated_data["medication"],
            dosage_amount=validated_data["dosage_amount"],
            dosage_unit=validated_data["dosage_unit_obj"],
            frequency_hours=validated_data["frequency_hours"],
            total_unit_amount=validated_data["total_unit_amount"],
            instructions=validated_data.get("instructions", ""),
        )


# NEW: update serializer (all fields writable; PATCH for partials, PUT for full)
class MedicationItemUpdateSerializer(serializers.Serializer):
    medication = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(), required=False
    )
    dosage_unit = serializers.CharField(required=False)
    dosage_amount = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    frequency_hours = serializers.IntegerField(min_value=1, required=False)
    total_unit_amount = serializers.IntegerField(min_value=1, required=False)
    instructions = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        # Map dosage_unit code -> object if provided
        if "dosage_unit" in data:
            try:
                data["dosage_unit_obj"] = DosageUnit.objects.get(code__iexact=data["dosage_unit"])
            except DosageUnit.DoesNotExist:
                raise serializers.ValidationError("Invalid dosage unit.")
        return data

    def update(self, instance: MedicationItem, validated_data):
        # Apply changes if present
        if "medication" in validated_data:
            instance.medication = validated_data["medication"]
        if "dosage_amount" in validated_data:
            instance.dosage_amount = validated_data["dosage_amount"]
        if "dosage_unit_obj" in validated_data:
            instance.dosage_unit = validated_data["dosage_unit_obj"]
        if "frequency_hours" in validated_data:
            instance.frequency_hours = validated_data["frequency_hours"]
        if "total_unit_amount" in validated_data:
            instance.total_unit_amount = validated_data["total_unit_amount"]
        if "instructions" in validated_data:
            instance.instructions = validated_data["instructions"]
        instance.save()
        return instance
