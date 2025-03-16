from rest_framework import serializers
from lab.models import Sample, SampleType
from patients.models import Patient


# Serializers
class SampleSerializer(serializers.ModelSerializer):
    patient_uuid = serializers.UUIDField(write_only=True)

    class Meta:
        model = Sample
        fields = ['id', 'patient_uuid', 'sample_type']

    def validate_patient_uuid(self, value):

        if not Patient.objects.filter(pid=value).exists():
            raise serializers.ValidationError("Patient not found.")
        return value

    def create(self, validated_data):
        patient = Patient.objects.get(pid=validated_data.pop('patient_uuid'))
        sample = Sample.objects.create(patient=patient, **validated_data)
        return sample


class SampleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleType
        fields = ['id', 'name', 'description', 'created_at']
