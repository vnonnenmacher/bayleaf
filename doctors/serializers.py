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
        fields = ["id", "doctor", "weekday", "service", "slot_duration", "from_time", "to_time"]
        extra_kwargs = {
            "doctor": {"read_only": True},
            "slot_duration": {"required": True, "min_value": 10, "max_value": 120},
            "from_time": {"required": True},
            "to_time": {"required": True}
        }


class ReducedDoctorSerializer(serializers.Serializer):
    """
    A reduced doctor serializer for embedding in slot responses.
    """
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()


class ServiceSlotSerializer(serializers.Serializer):
    """
    Serializer for service slots.
    """
    doctor = ReducedDoctorSerializer()
    service_id = serializers.IntegerField()
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")

    def to_representation(self, instance):
        """
        Ensure we are working with a dictionary, not an object.
        """
        if isinstance(instance, dict):
            return instance  # Already a dictionary, return as is
        return {
            "doctor": {
                "id": instance.doctor_id,
                "first_name": instance.doctor_name.split(" ")[0],  # Extract first name
                "last_name": instance.doctor_name.split(" ")[1] if " " in instance.doctor_name else "",
                "email": instance.doctor_email,
            },
            "service_id": instance.service_id,
            "start_time": instance.start_time.strftime("%H:%M"),
            "end_time": instance.end_time.strftime("%H:%M"),
        }
