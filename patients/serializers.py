from rest_framework import serializers
from .models import Patient
from core.serializers import AddressSerializer, ContactSerializer


class PatientSerializer(serializers.ModelSerializer):
    """Serializer for the Patient model with Address & Contact fields."""

    address1 = AddressSerializer(required=False)
    address2 = AddressSerializer(required=False)
    primary_contact = ContactSerializer(required=False)
    secondary_contact = ContactSerializer(required=False)

    class Meta:
        model = Patient
        fields = [
            "pid",
            "first_name",
            "last_name",
            "birth_date",
            "address1",
            "address2",
            "primary_contact",
            "secondary_contact"
        ]

    def update(self, instance, validated_data):
        """Custom update method to handle nested Address & Contact data."""
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)

        # Update the base Patient fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle Address1
        if address1_data:
            if instance.address1:
                for attr, value in address1_data.items():
                    setattr(instance.address1, attr, value)
                instance.address1.save()
            else:
                instance.address1 = AddressSerializer.create(AddressSerializer(), validated_data=address1_data)

        # Handle Address2
        if address2_data:
            if instance.address2:
                for attr, value in address2_data.items():
                    setattr(instance.address2, attr, value)
                instance.address2.save()
            else:
                instance.address2 = AddressSerializer.create(AddressSerializer(), validated_data=address2_data)

        # Handle Primary Contact
        if primary_contact_data:
            if instance.primary_contact:
                for attr, value in primary_contact_data.items():
                    setattr(instance.primary_contact, attr, value)
                instance.primary_contact.save()
            else:
                instance.primary_contact = ContactSerializer.create(ContactSerializer(),
                                                                    validated_data=primary_contact_data)

        # Handle Secondary Contact
        if secondary_contact_data:
            if instance.secondary_contact:
                for attr, value in secondary_contact_data.items():
                    setattr(instance.secondary_contact, attr, value)
                instance.secondary_contact.save()
            else:
                instance.secondary_contact = ContactSerializer.create(ContactSerializer(),
                                                                      validated_data=secondary_contact_data)

        instance.save()
        return instance
