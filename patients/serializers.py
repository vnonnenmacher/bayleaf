from rest_framework import serializers
from patients.models import Patient
from users.models import Identifier, IdentifierType
from core.serializers import AddressSerializer, ContactSerializer
from core.models import Address, Contact
from users.serializers import IdentifierSerializer


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for Patient with Identifiers, Address & Contact."""

    address1 = AddressSerializer(required=False)
    address2 = AddressSerializer(required=False)
    primary_contact = ContactSerializer(required=False)
    secondary_contact = ContactSerializer(required=False)
    identifiers = IdentifierSerializer(many=True, required=False)

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
        ]
        extra_kwargs = {"password": {"write_only": True},
                        "pid": {"read_only": True}}

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

        # Create and link Addresses
        if address1_data:
            patient.address1 = AddressSerializer.create(AddressSerializer(), validated_data=address1_data)
        if address2_data:
            patient.address2 = AddressSerializer.create(AddressSerializer(), validated_data=address2_data)

        # Create and link Contacts
        if primary_contact_data:
            patient.primary_contact = ContactSerializer.create(ContactSerializer(), validated_data=primary_contact_data)
        if secondary_contact_data:
            patient.secondary_contact = ContactSerializer.create(ContactSerializer(),
                                                                 validated_data=secondary_contact_data)

        patient.save()

        # Handle Identifiers
        for identifier_data in identifiers_data:
            identifier_type_name = identifier_data.get("type")
            identifier_value = identifier_data.get("value")

            if identifier_type_name and identifier_value:
                # ✅ Fix: Make sure to get `IdentifierType` object instead of passing a string
                identifier_type, _ = IdentifierType.objects.get_or_create(name=identifier_type_name)

                Identifier.objects.update_or_create(
                    user=patient,
                    type=identifier_type,  # ✅ Ensures correct reference to IdentifierType (string PK)
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

        # ✅ Update base Patient fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # ✅ Update or Create Address1
        if address1_data:
            if instance.address1:
                for key, value in address1_data.items():
                    setattr(instance.address1, key, value)
                instance.address1.save()
            else:
                instance.address1 = Address.objects.create(**address1_data)

        # ✅ Update or Create Address2
        if address2_data:
            if instance.address2:
                for key, value in address2_data.items():
                    setattr(instance.address2, key, value)
                instance.address2.save()
            else:
                instance.address2 = Address.objects.create(**address2_data)

        # ✅ Update or Create Primary Contact
        if primary_contact_data:
            if instance.primary_contact:
                for key, value in primary_contact_data.items():
                    setattr(instance.primary_contact, key, value)
                instance.primary_contact.save()
            else:
                instance.primary_contact = Contact.objects.create(**primary_contact_data)

        # ✅ Update or Create Secondary Contact
        if secondary_contact_data:
            if instance.secondary_contact:
                for key, value in secondary_contact_data.items():
                    setattr(instance.secondary_contact, key, value)
                instance.secondary_contact.save()
            else:
                instance.secondary_contact = Contact.objects.create(**secondary_contact_data)

        instance.save()

        # ✅ Update or Create Identifiers
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
        fields = ['pid', 'first_name', 'last_name', 'birth_date']
