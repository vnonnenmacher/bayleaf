from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = Patient
        fields = ["pid", "email", "password", "first_name", "last_name", "birth_date"]
        extra_kwargs = {
            "pid": {"read_only": True},  # Patients cannot modify their own PID
            "email": {"read_only": True}  # Ensure email remains immutable
        }

    def create(self, validated_data):
        """Create a new patient with encrypted password"""
        password = validated_data.pop("password", None)
        patient = Patient.objects.create_user(**validated_data)
        if password:
            patient.set_password(password)
            patient.save()
        return patient
