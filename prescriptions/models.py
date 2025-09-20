import uuid
from django.db import models
from professionals.models import Professional
from patients.models import Patient


class AbstractPrescription(models.Model):
    """
    Abstract base class for any type of prescription (e.g. medications, treatments, labs).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name="%(class)s_prescriptions"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="%(class)s_prescriptions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class AbstractPrescriptionItem(models.Model):
    """
    Abstract base class for an item in a prescription (e.g. a single medication, test, etc.)
    """
    prescription = models.ForeignKey(
        "prescriptions.Prescription",  # to be overridden in concrete classes
        on_delete=models.CASCADE,
        related_name="items"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="%(class)s_items"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
