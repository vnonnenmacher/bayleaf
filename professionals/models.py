import uuid
from django.db import models
from users.models import User, Person

from core.models import Service


class Specialization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Professional(User, Person):
    did = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    services = models.ManyToManyField(Service, related_name="professionals", blank=True)
    specializations = models.ManyToManyField(Specialization, related_name="professionals", blank=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Professional"
        verbose_name_plural = "Professionals"

    def __str__(self):
        return f"Professional {self.did}: {self.email}. Role {self.role}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


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

    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name="shifts")
    weekday = models.IntegerField(choices=WEEKDAYS)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="shifts")
    slot_duration = models.PositiveIntegerField(default=30)  # Default slot duration in minutes
    from_time = models.TimeField()  # ✅ Shift start time
    to_time = models.TimeField()  # ✅ Shift end time

    class Meta:
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"
        unique_together = ("professional", "weekday", "service", "from_time", "to_time")

    def __str__(self):
        return (f"{self.professional.email} - {self.get_weekday_display()} ("
                f"{self.service.name}) [{self.from_time} - {self.to_time}]")
