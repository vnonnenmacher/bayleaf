from rest_framework import serializers
from .models import Shift
from .models import Doctor
from core.serializers import AddressSerializer, ContactSerializer
from core.models import Address, Contact


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for creating a Doctor with Address & Contact fields."""
    
    address1 = AddressSerializer(required=False)
    address2 = AddressSerializer(required=False)
    primary_contact = ContactSerializer(required=False)
    secondary_contact = ContactSerializer(required=False)

    class Meta:
        model = Doctor
        fields = [
            "did", 
            "first_name", 
            "last_name", 
            "birth_date", 
            "email", 
            "password", 
            "address1", 
            "address2", 
            "primary_contact", 
            "secondary_contact"
        ]
        extra_kwargs = {"password": {"write_only": True}}  # Make password write-only

    def create(self, validated_data):
        """Handles nested Address and Contact creation when creating a Doctor."""

        # Extract nested data
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)

        # Create doctor (without address and contact)
        doctor = Doctor.objects.create(**validated_data)
        doctor.set_password(validated_data["password"])  # Hash password
        doctor.save()

        # Create and link Address1 if provided
        if address1_data:
            doctor.address1 = Address.objects.create(**address1_data)

        # Create and link Address2 if provided
        if address2_data:
            doctor.address2 = Address.objects.create(**address2_data)

        # Create and link Primary Contact if provided
        if primary_contact_data:
            doctor.primary_contact = Contact.objects.create(**primary_contact_data)

        # Create and link Secondary Contact if provided
        if secondary_contact_data:
            doctor.secondary_contact = Contact.objects.create(**secondary_contact_data)

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
