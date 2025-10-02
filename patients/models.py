import uuid
from django.db import models
from users.models import User, Person  # Import from users app


class Patient(User, Person):
    pid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.email}"
