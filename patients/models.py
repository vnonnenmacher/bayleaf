from django.db import models
from users.models import User, Person  # Import from users app

class Patient(User, Person):
    pid = models.CharField(max_length=50, primary_key=True)  # Custom Patient ID

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"Patient {self.pid}: {self.email}"