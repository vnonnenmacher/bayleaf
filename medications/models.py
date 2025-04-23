from django.db import models
from core.models import DosageUnit
from prescriptions.models import AbstractPrescription, AbstractPrescriptionItem
from professionals.models import Professional
from patients.models import Patient

class Medication(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MedicationPrescription(AbstractPrescription):
    """
    A prescription that includes one or more medications.
    """
    # Inherits:
    # - UUID primary key (`id`)
    # - professional
    # - patient
    # - created_at

    class Meta:
        verbose_name = "Medication Prescription"
        verbose_name_plural = "Medication Prescriptions"


class MedicationItem(AbstractPrescriptionItem):
    """
    Represents a single medication item within a prescription.
    """
    prescription = models.ForeignKey(
        MedicationPrescription,
        on_delete=models.CASCADE,
        related_name="medication_items"
    )
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage_amount = models.DecimalField(max_digits=6, decimal_places=2)
    dosage_unit = models.ForeignKey(DosageUnit, on_delete=models.PROTECT)
    frequency_hours = models.PositiveIntegerField(help_text="Interval between doses, in hours.")
    start_date = models.DateField()
    end_date = models.DateField()
    instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medication.name} ({self.dosage_amount} {self.dosage_unit.code})"