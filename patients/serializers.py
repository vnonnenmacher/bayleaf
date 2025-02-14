from rest_framework import serializers
from .models import Patient


class PatientCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Patient
        fields = ["pid", "email", "password", "first_name", "last_name", "birth_date"]

    def create(self, validated_data):
        """Create a new patient with encrypted password"""
        password = validated_data.pop("password")  # Extract password
        patient = Patient.objects.create_user(**validated_data)  # Create patient
        patient.set_password(password)  # Hash password
        patient.save()
        return patient
