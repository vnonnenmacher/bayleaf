from rest_framework import serializers
from .models import Shift
from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = Doctor
        fields = ["did", "email", "password", "first_name", "last_name", "birth_date"]
        extra_kwargs = {
            "did": {"read_only": True},  # DID should not be editable after creation
            "email": {"read_only": False}  # Allow email to be passed correctly
        }

    def create(self, validated_data):
        """Create a new doctor with an encrypted password"""
        password = validated_data.pop("password", None)
        email = validated_data.pop("email")  # Extract email explicitly

        doctor = Doctor.objects.create_user(email=email, **validated_data)  # Pass email correctly
        if password:
            doctor.set_password(password)
            doctor.save()
        return doctor


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["id", "doctor", "weekday", "service"]
        extra_kwargs = {
            "doctor": {"read_only": True}  # Ensure doctor is always set automatically
        }
