from django.db import models
from core.models import DosageUnit
from events.models import ScheduledCheckpointEvent
from prescriptions.models import AbstractPrescription, AbstractPrescriptionItem


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
    Represents a single medication item prescription.
    """
    prescription = models.ForeignKey(
        MedicationPrescription,
        on_delete=models.CASCADE,
        related_name="medication_items",
        null=True
    )
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage_amount = models.DecimalField(max_digits=6, decimal_places=2)
    dosage_unit = models.ForeignKey(DosageUnit, on_delete=models.PROTECT)
    frequency_hours = models.PositiveIntegerField(help_text="Interval between doses, in hours.")
    instructions = models.TextField(blank=True)
    total_unit_amount = models.PositiveIntegerField(
        help_text="Total number of units (e.g., capsules, tablets) to be taken over the course."
    )

    def __str__(self):
        return f"{self.medication.name} ({self.dosage_amount} {self.dosage_unit.code})"


class TakeMedicationEvent(ScheduledCheckpointEvent):
    """
    Represents a scheduled event for a patient to take a medication.
    Can optionally be linked to a prescription.
    """

    medication_item = models.ForeignKey(
        MedicationItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="medication_events"
    )

    class Meta:
        verbose_name = "Take Medication Event"
        verbose_name_plural = "Take Medication Events"

    def __str__(self):
        return f"{self.medication_item.medication.name} for {self.medication_item.patient} at {self.scheduled_to_complete_from}"
