from rest_framework import serializers
from appointments.models import Appointment
from doctors.models import Doctor
from patients.models import Patient
from core.models import Service


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Appointment model.
    Ensures correct handling of event-based fields and relationships.
    """

    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor",
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
