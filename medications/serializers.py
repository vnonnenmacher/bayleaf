from rest_framework import serializers
from core.serializers import DosageUnitSerializer
from patients.models import Patient
from professionals.models import Professional
from core.models import DosageUnit
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
    # Return the full medication object (not just the ID)
    medication = MedicationSerializer(read_only=True)
    # Keep dosage_unit readable too (code + name); if you prefer just code, swap to StringRelatedField.
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
