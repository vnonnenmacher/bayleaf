import uuid
from django.db import models
from users.models import User, Person  # Import from users app
from django.db import models
from django.utils import timezone


class Patient(User, Person):
    pid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.email}"


class Relative(User, Person):
    """
    A family member / caregiver who can log in just like any other user.
    Inherits the concrete PK from `User` (no extra primary key needed).
    """
    # Many-to-many to patients, through a join model (so we can add fields later).
    patients = models.ManyToManyField(
        'patients.Patient',
        through='PatientRelationship',
        related_name='relatives',
        blank=True,
    )

    class Meta:
        verbose_name = "Relative"
        verbose_name_plural = "Relatives"

    def __str__(self):
        # fall back to email or a readable name
        return self.get_full_name() or self.email or f"Relative #{self.pk}"


class PatientRelationship(models.Model):
    """
    Join table for Relative <-> Patient.
    Keep it minimal now; we can enrich later with role/scopes/consent, etc.
    """
    relative = models.ForeignKey(
        'patients.Relative',
        on_delete=models.CASCADE,
        related_name='patient_relationships',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='relative_relationships',
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('relative', 'patient')
        verbose_name = "Patient Relationship"
        verbose_name_plural = "Patient Relationships"

    def __str__(self):
        return f"{self.relative} ↔ {self.patient}"