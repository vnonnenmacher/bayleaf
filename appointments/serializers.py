from rest_framework import serializers
from appointments.models import Appointment
from professionals.models import Professional, Shift
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
    shift_id = serializers.PrimaryKeyRelatedField(queryset=Shift.objects.all(), source="shift")
    appointment_time = serializers.DateTimeField(write_only=True)

    class Meta:
        model = Appointment
        fields = ["id", "shift_id", "appointment_time"]
        read_only_fields = ["id"]

    def validate(self, data):
        shift = data["shift"]
        scheduled_to = data["appointment_time"]

        # ✅ Make sure the appointment is in the future
        if scheduled_to <= now():
            raise serializers.ValidationError("Appointment time must be in the future.")

        # ✅ Check that appointment_time fits within shift's time range
        # shift_date = scheduled_to.date()
        shift_start = shift.from_time
        shift_end = shift.to_time

        if not (shift_start <= scheduled_to.time() < shift_end):
            raise serializers.ValidationError("Selected time is outside the shift bounds.")

        data["professional"] = shift.professional
        data["service"] = shift.service
        data["duration_minutes"] = shift.slot_duration
        data["scheduled_to"] = scheduled_to

        # Inject patient and creator from context
        request = self.context.get("request")
        if request and request.user:
            data["created_by"] = request.user
            try:
                data["patient"] = Patient.objects.get(user_ptr_id=request.user.id)
            except Patient.DoesNotExist:
                raise serializers.ValidationError("Authenticated user is not a patient.")

        return data

    def create(self, validated_data):
        validated_data["event_type"] = "appointment"
        return Appointment.objects.create(**validated_data)
