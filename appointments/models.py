from django.db import models
from doctors.models import Doctor, Shift
from patients.models import Patient
from core.models import Service


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested"),
        ("confirmed", "Confirmed"),
        ("initiated", "Initiated"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="appointments")
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")

    booked_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when it was booked
    scheduled_to = models.DateTimeField()  # Scheduled time of appointment
    completed_at = models.DateTimeField(null=True, blank=True)  # When appointment was completed
    duration = models.PositiveIntegerField()  # Duration in minutes

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        unique_together = ("doctor", "patient", "scheduled_to")  # Prevent duplicate bookings

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.email} for {self.patient.email} on {self.scheduled_to}"
