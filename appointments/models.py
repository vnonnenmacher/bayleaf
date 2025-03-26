from django.db import models
from professionals.models import Professional, Shift
from patients.models import Patient
from core.models import Service
from events.models import ScheduledTimedEvent  # Import the base event model


class Appointment(ScheduledTimedEvent):
    """
    Model representing a booked appointment between a doctor and a patient.
    """

    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="appointments")
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.email} for {self.patient.email} on {self.scheduled_to}"

    def save(self, *args, **kwargs):
        """Ensure event_type is always 'appointment'."""
        self.event_type = "appointment"
        super().save(*args, **kwargs)
