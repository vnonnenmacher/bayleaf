from rest_framework import serializers
from appointments.models import Appointment
from professionals.models import Professional, ServiceSlot
from patients.models import Patient
from core.models import Service
from django.utils.timezone import now


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    Ensures correct handling of event-based fields and relationships.
    """

    professional = serializers.PrimaryKeyRelatedField(queryset=Professional.objects.all())
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = Appointment
        fields = [
            "id",
            "professional",
            "patient",
            "service",
            "shift",
            "scheduled_to",
            "duration_minutes",
            "status",
            "created_by",
            "created_at",
            "rescheduled_to",
        ]
        read_only_fields = ["id", "created_by", "created_at", "status", "rescheduled_to"]

    def validate_scheduled_to(self, value):
        """Ensure the appointment is scheduled for a future date/time."""
        from django.utils.timezone import now
        if value <= now():
            raise serializers.ValidationError("The scheduled time must be in the future.")
        return value

    def create(self, validated_data):
        """Ensure event_type is always 'appointment' and assign the created_by user."""
        validated_data["event_type"] = "appointment"
        request = self.context.get("request")
        if request and request.user:
            validated_data["created_by"] = request.user  # Assign logged-in user
        return super().create(validated_data)


class AppointmentBookingSerializer(serializers.ModelSerializer):
    service_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceSlot.objects.all(), source="service_slot", write_only=True
    )

    class Meta:
        model = Appointment
        fields = ["id", "service_slot_id"]
        read_only_fields = ["id"]

    def validate(self, data):
        slot = data["service_slot"]

        if slot.start_time <= now():
            raise serializers.ValidationError("Slot must be in the future.")

        # Ensure slot is not already booked (except by a canceled appointment)
        if Appointment.objects.filter(service_slot=slot).exclude(status="CANCELED").exists():
            raise serializers.ValidationError("This slot is already booked.")

        data["professional"] = slot.shift.professional
        data["service"] = slot.shift.service
        data["scheduled_to"] = slot.start_time
        data["duration_minutes"] = (slot.end_time - slot.start_time).seconds // 60

        # Attach patient
        request = self.context.get("request")
        if request and request.user:
            try:
                data["patient"] = Patient.objects.get(user_ptr_id=request.user.id)
            except Patient.DoesNotExist:
                raise serializers.ValidationError("Authenticated user is not a patient.")

        return data

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and "created_by" not in validated_data:
            validated_data["created_by"] = request.user
        validated_data["event_type"] = "appointment"
        return Appointment.objects.create(**validated_data)


class AppointmentListSerializer(serializers.ModelSerializer):
    professional_did = serializers.UUIDField(source="professional.did", read_only=True)
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "scheduled_to",
            "duration_minutes",
            "status",
            "professional_did",
            "patient",
            "service",
            "service_slot",
        ]
