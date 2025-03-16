from django.db import models
from django.contrib.auth import get_user_model
import uuid


class SampleState(models.Model):
    """
    Represents a state in the sample's lifecycle (e.g., Collected, Transported, Stored).
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SampleType(models.Model):
    """
    Represents the type of biological sample (e.g., Blood, Tissue, Urine).
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Sample(models.Model):
    """
    Represents a biological sample collected from a patient.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="samples")
    sample_type = models.ForeignKey(SampleType, on_delete=models.CASCADE, related_name="samples")

    def __str__(self):
        return f"Sample {self.id} - {self.sample_type.name}"

    def get_current_state(self):
        """Retrieves the latest verified state transition."""
        latest_transition = self.state_transitions.filter(is_verified=True).order_by('-created_at').first()
        return latest_transition.new_state if latest_transition else None


class SampleStateTransition(models.Model):
    """
    Tracks state transitions for a sample and links them to blockchain records.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name="state_transitions")
    previous_state = models.ForeignKey(SampleState, on_delete=models.SET_NULL, null=True, related_name="previous_transitions")
    new_state = models.ForeignKey(SampleState, on_delete=models.CASCADE, related_name="new_transitions")
    changed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(blank=True, null=True)  # Timestamp when the transition was validated

    # Blockchain validation
    is_valid = models.BooleanField(default=None, null=True)  # Null until blockchain validation happens
    validation_message = models.TextField(blank=True, null=True)  # Reason for rejection, if any

    # Blockchain record
    transaction_hash = models.CharField(max_length=128, unique=True, blank=True, null=True)  # Blockchain transaction hash
    blockchain_timestamp = models.DateTimeField(blank=True, null=True)  # Timestamp of blockchain transaction
    is_verified = models.BooleanField(default=False)  # True when transaction is confirmed on-chain

    metadata = models.JSONField(blank=True, null=True)  # Extra metadata

    def __str__(self):
        return f"Sample {self.sample.id}: {self.previous_state} → {self.new_state} at {self.created_at}"
