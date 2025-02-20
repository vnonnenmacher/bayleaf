from django.db import models
from users.models import User, Person

from core.models import Service


class Doctor(User, Person):
    did = models.CharField(max_length=50, primary_key=True)  # Doctor ID as Primary Key

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self):
        return f"Doctor {self.did}: {self.email}"


class Shift(models.Model):
    WEEKDAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="shifts")
    weekday = models.IntegerField(choices=WEEKDAYS)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="shifts")

    class Meta:
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"
        unique_together = ("doctor", "weekday", "service")  # Prevent duplicate shifts

    def __str__(self):
        return f"{self.doctor.email} - {self.get_weekday_display()} ({self.service.name})"
