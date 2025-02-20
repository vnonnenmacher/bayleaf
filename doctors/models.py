from django.db import models
from users.models import User, Person


class Doctor(User, Person):
    did = models.CharField(max_length=50, primary_key=True)  # Doctor ID as Primary Key

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self):
        return f"Doctor {self.did}: {self.email}"
