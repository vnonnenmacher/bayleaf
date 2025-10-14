# patients/serializers.py
from __future__ import annotations

import uuid
from typing import Any, Dict

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.models import Address, Contact
from core.serializers import AddressSerializer, ContactSerializer

from users.models import Identifier, IdentifierType, User
from users.serializers import IdentifierSerializer

from patients.models import (
    Patient,
    Relative,
    PatientRelationship,  # has `active = models.BooleanField(default=True)`
)


# =========================================
# Helpers (placeholder email + auth checks)
# =========================================

PLACEHOLDER_DOMAIN = "placeholder.local"

def _placeholder_email() -> str:
    """Unique, valid-looking email to satisfy unique=True constraint on User.email."""
    return f"noemail+{uuid.uuid4().hex[:20]}@{PLACEHOLDER_DOMAIN}"

def _require_relative(request_user: User) -> Relative:
    """
    Ensure the logged-in user is a Relative (multi-table inheritance).
    Access via request.user.relative; will exist only if this user row has a Relative child.
    """
    rel = getattr(request_user, "relative", None)
    if not isinstance(rel, Relative):
        raise ValidationError("Logged-in user is not a Relative.")
    return rel


# =========================
# Patient (existing) CRUD
# =========================

class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient with Identifiers, Address & Contact."""
    address1 = AddressSerializer(required=False)
    address2 = AddressSerializer(required=False)
    primary_contact = ContactSerializer(required=False)
    secondary_contact = ContactSerializer(required=False)
    identifiers = IdentifierSerializer(many=True, required=False)
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Patient
        fields = [
            "pid",
            "first_name",
            "last_name",
            "birth_date",
            "email",
            "password",
            "address1",
            "address2",
            "primary_contact",
            "secondary_contact",
            "identifiers",
            "avatar",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "pid": {"read_only": True},
        }

    def create(self, validated_data):
        """Handles nested creation of Identifiers, Address & Contact."""
        identifiers_data = validated_data.pop("identifiers", [])
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)

        # Create patient without relations
        patient = Patient.objects.create(**validated_data)
        patient.set_password(validated_data["password"])
        patient.save()

        # Addresses
        if address1_data:
            patient.address1 = AddressSerializer.create(AddressSerializer(), validated_data=address1_data)
        if address2_data:
            patient.address2 = AddressSerializer.create(AddressSerializer(), validated_data=address2_data)

        # Contacts
        if primary_contact_data:
            patient.primary_contact = ContactSerializer.create(ContactSerializer(), validated_data=primary_contact_data)
        if secondary_contact_data:
            patient.secondary_contact = ContactSerializer.create(ContactSerializer(), validated_data=secondary_contact_data)

        patient.save()

        # Identifiers
        for identifier_data in identifiers_data:
            identifier_type_name = identifier_data.get("type")
            identifier_value = identifier_data.get("value")
            if identifier_type_name and identifier_value:
                identifier_type, _ = IdentifierType.objects.get_or_create(name=identifier_type_name)
                Identifier.objects.update_or_create(
                    user=patient,
                    type=identifier_type,
                    defaults={"value": identifier_value},
                )

        return patient

    def update(self, instance, validated_data):
        """Handles nested updates of Identifiers, Address & Contact."""
        identifiers_data = validated_data.pop("identifiers", [])
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)

        # Base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Address1
        if address1_data:
            if instance.address1:
                for k, v in address1_data.items():
                    setattr(instance.address1, k, v)
                instance.address1.save()
            else:
                instance.address1 = Address.objects.create(**address1_data)

        # Address2
        if address2_data:
            if instance.address2:
                for k, v in address2_data.items():
                    setattr(instance.address2, k, v)
                instance.address2.save()
            else:
                instance.address2 = Address.objects.create(**address2_data)

        # Primary contact
        if primary_contact_data:
            if instance.primary_contact:
                for k, v in primary_contact_data.items():
                    setattr(instance.primary_contact, k, v)
                instance.primary_contact.save()
            else:
                instance.primary_contact = Contact.objects.create(**primary_contact_data)

        # Secondary contact
        if secondary_contact_data:
            if instance.secondary_contact:
                for k, v in secondary_contact_data.items():
                    setattr(instance.secondary_contact, k, v)
                instance.secondary_contact.save()

        instance.save()

        # Identifiers
        for identifier_data in identifiers_data:
            identifier_type_name = identifier_data.get("type")
            identifier_value = identifier_data.get("value")
            if identifier_type_name and identifier_value:
                identifier_type, _ = IdentifierType.objects.get_or_create(name=identifier_type_name)
                Identifier.objects.update_or_create(
                    user=instance,
                    type=identifier_type,
                    defaults={"value": identifier_value},
                )

        return instance


class ReducedPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["pid", "first_name", "last_name", "birth_date"]


# ===================================================
# Relative + PatientRelationship (final set)
# ===================================================

# ---- Patient brief (for embedding in relationship reads)
class PatientBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["pid", "first_name", "last_name", "email", "birth_date", "is_active"]


# ---- Read relationship (embeds patient)
class PatientRelationshipReadSerializer(serializers.ModelSerializer):
    patient = PatientBriefSerializer(read_only=True)

    class Meta:
        model = PatientRelationship
        fields = ["id", "patient", "active", "created_at"]


# ---- Unified Relative serializer: create, retrieve (with links), update (nested)
class RelativeSerializer(serializers.ModelSerializer):
    # Write-only for create
    password = serializers.CharField(write_only=True, min_length=6, required=False)

    # Optional
    birth_date = serializers.DateField(required=False, allow_null=True)

    # Nested read/write
    address1 = AddressSerializer(required=False, allow_null=True)
    address2 = AddressSerializer(required=False, allow_null=True)
    primary_contact = ContactSerializer(required=False, allow_null=True)
    secondary_contact = ContactSerializer(required=False, allow_null=True)

    # Read-only: relationships with embedded patients
    patient_links = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Relative
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "birth_date",
            "password",          # write-only (create)
            "address1",
            "address2",
            "primary_contact",
            "secondary_contact",
            "patient_links",     # read-only
        ]
        read_only_fields = ["id", "patient_links"]

    # ---------- READ ----------
    def get_patient_links(self, obj: Relative):
        qs = obj.patient_relationships.select_related("patient").order_by("-created_at")
        return PatientRelationshipReadSerializer(qs, many=True).data

    # ---------- CREATE ----------
    def create(self, validated_data: Dict[str, Any]) -> Relative:
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)

        password = validated_data.pop("password", None)
        if not password:
            raise ValidationError({"password": "This field is required when creating a Relative."})

        rel = Relative.objects.create(**validated_data, is_active=True)
        rel.set_password(password)
        rel.save(update_fields=["password"])

        if address1_data:
            rel.address1 = Address.objects.create(**address1_data)
        if address2_data:
            rel.address2 = Address.objects.create(**address2_data)
        if primary_contact_data:
            rel.primary_contact = Contact.objects.create(**primary_contact_data)
        if secondary_contact_data:
            rel.secondary_contact = Contact.objects.create(**secondary_contact_data)
        rel.save()

        return rel

    # ---------- UPDATE ----------
    def update(self, instance: Relative, validated_data: Dict[str, Any]) -> Relative:
        # Don’t change password here
        validated_data.pop("password", None)

        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)

        # Scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Address1
        if address1_data is not None:
            if instance.address1:
                for k, v in address1_data.items():
                    setattr(instance.address1, k, v)
                instance.address1.save()
            else:
                instance.address1 = Address.objects.create(**address1_data)

        # Address2
        if address2_data is not None:
            if instance.address2:
                for k, v in address2_data.items():
                    setattr(instance.address2, k, v)
                instance.address2.save()
            else:
                instance.address2 = Address.objects.create(**address2_data)

        # Primary contact
        if primary_contact_data is not None:
            if instance.primary_contact:
                for k, v in primary_contact_data.items():
                    setattr(instance.primary_contact, k, v)
                instance.primary_contact.save()
            else:
                instance.primary_contact = Contact.objects.create(**primary_contact_data)

        # Secondary contact
        if secondary_contact_data is not None:
            if instance.secondary_contact:
                for k, v in secondary_contact_data.items():
                    setattr(instance.secondary_contact, k, v)
                instance.secondary_contact.save()
            else:
                instance.secondary_contact = Contact.objects.create(**secondary_contact_data)

        instance.save()
        return instance


# ---- Relative creates a *new* managed Patient and links it
class AddManagedPatientSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    birth_date = serializers.DateField(required=False, allow_null=True)
    active = serializers.BooleanField(default=True)  # relationship.active

    def validate(self, attrs):
        # Make sure callers don't try to set patient email
        if "email" in getattr(self, "initial_data", {}):
            raise ValidationError("Do not send 'email'—it is generated by the backend.")
        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> PatientRelationship:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise ValidationError("Authentication required.")

        relative = _require_relative(request.user)

        # Backend-generated placeholder email; patient cannot log in yet.
        patient = Patient.objects.create(
            email=_placeholder_email(),
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            birth_date=validated_data.get("birth_date"),
            is_active=False,
        )
        patient.set_unusable_password()
        patient.save(update_fields=["password"])

        rel = PatientRelationship.objects.create(
            relative=relative,
            patient=patient,
            active=validated_data.get("active", True),
            created_at=timezone.now(),
        )
        return rel

    def to_representation(self, instance: PatientRelationship) -> Dict[str, Any]:
        return PatientRelationshipReadSerializer(instance).data


# ---- Relative links an *existing* Patient
class LinkExistingPatientSerializer(serializers.Serializer):
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(), source="patient"
    )
    active = serializers.BooleanField(default=True)

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> PatientRelationship:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise ValidationError("Authentication required.")

        relative = _require_relative(request.user)
        patient: Patient = validated_data["patient"]

        if PatientRelationship.objects.filter(relative=relative, patient=patient).exists():
            raise ValidationError("This patient is already linked to the relative.")

        rel = PatientRelationship.objects.create(
            relative=relative,
            patient=patient,
            active=validated_data.get("active", True),
            created_at=timezone.now(),
        )
        return rel

    def to_representation(self, instance: PatientRelationship) -> Dict[str, Any]:
        return PatientRelationshipReadSerializer(instance).data


# ---- Toggle (in)active on the relationship (no delete)
class PatientRelationshipToggleActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientRelationship
        fields = ["id", "active"]

    def update(self, instance: PatientRelationship, validated_data: Dict[str, Any]) -> PatientRelationship:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise ValidationError("Authentication required.")

        relative = _require_relative(request.user)
        if instance.relative_id != relative.id:
            raise ValidationError("You cannot modify relationships that are not yours.")

        instance.active = validated_data["active"]
        instance.save(update_fields=["active"])
        return instance
