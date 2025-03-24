from rest_framework import serializers

from users.models import Identifier, IdentifierType
from users.serializers import IdentifierSerializer
from professionals.models import Role, Shift, Professional, Specialization
from core.serializers import AddressSerializer, ContactSerializer
from core.models import Address, Contact


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = ["id", "name", "description"]
        extra_kwargs = {
            "name": {"required": True},
            "description": {"required": False}
        }


class ProfessionalSerializer(serializers.ModelSerializer):
    """Serializer for Professional with Identifiers, Address & Contact."""

    address1 = AddressSerializer(required=False)
    address2 = AddressSerializer(required=False)
    primary_contact = ContactSerializer(required=False)
    secondary_contact = ContactSerializer(required=False)
    identifiers = IdentifierSerializer(many=True, required=False)  # ✅ Handles identifier updates
    role = RoleSerializer(required=False)
    role_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Professional
        fields = [
            "did",
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
            "role",
            "role_id"
        ]
        extra_kwargs = {"password": {"write_only": True},
                        "did": {"read_only": True}}

    def create(self, validated_data):
        """Handles nested creation of Identifiers, Address & Contact."""
        identifiers_data = validated_data.pop("identifiers", [])
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)
        role_id = validated_data.pop("role_id", None)

        # ✅ Create professional without relations
        professional = Professional.objects.create(**validated_data)
        professional.set_password(validated_data["password"])
        professional.save()

        # ✅ Handle Address1
        if address1_data:
            professional.address1 = Address.objects.create(**address1_data)

        # ✅ Handle Address2
        if address2_data:
            professional.address2 = Address.objects.create(**address2_data)

        # ✅ Handle Primary Contact
        if primary_contact_data:
            professional.primary_contact = Contact.objects.create(**primary_contact_data)

        # ✅ Handle Secondary Contact
        if secondary_contact_data:
            professional.secondary_contact = Contact.objects.create(**secondary_contact_data)

        professional.save()

        # ✅ Handle Identifiers (Fix: Ensure `IdentifierType` is found or created)
        for identifier_data in identifiers_data:
            identifier_type_name = identifier_data.get("type")
            identifier_value = identifier_data.get("value")

            if identifier_type_name and identifier_value:
                identifier_type, _ = IdentifierType.objects.get_or_create(name=identifier_type_name)

                Identifier.objects.create(
                    user=professional,
                    type=identifier_type,  # ✅ Assign valid IdentifierType instance
                    value=identifier_value,
                )

        if role_id:
            professional.role = Role.objects.get(id=role_id)

        return professional

    def update(self, instance, validated_data):
        """Handles nested updates of Identifiers, Address & Contact."""
        identifiers_data = validated_data.pop("identifiers", [])
        address1_data = validated_data.pop("address1", None)
        address2_data = validated_data.pop("address2", None)
        primary_contact_data = validated_data.pop("primary_contact", None)
        secondary_contact_data = validated_data.pop("secondary_contact", None)
        role_id = validated_data.pop("role_id", None)

        print("role_id", role_id)

        # ✅ Update base Professional fields
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

        if role_id:
            instance.role = Role.objects.get(id=role_id)

        instance.save()

        return instance


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["id", "professional", "weekday", "service", "slot_duration", "from_time", "to_time"]
        extra_kwargs = {
            "professional": {"read_only": True},
            "slot_duration": {"required": True, "min_value": 10, "max_value": 120},
            "from_time": {"required": True},
            "to_time": {"required": True}
        }


class ReducedProfessionalSerializer(serializers.Serializer):
    """
    A reduced professional serializer for embedding in slot responses.
    """
    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()


class ServiceSlotSerializer(serializers.Serializer):
    """
    Serializer for service slots.
    """
    professional = ReducedProfessionalSerializer()
    service_id = serializers.IntegerField()
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")

    def to_representation(self, instance):
        """
        Ensure we are working with a dictionary, not an object.
        """
        if isinstance(instance, dict):
            return instance  # Already a dictionary, return as is
        return {
            "professional": {
                "id": instance.professional_id,
                "first_name": instance.professional_name.split(" ")[0],  # Extract first name
                "last_name": instance.professional_name.split(" ")[1] if " " in instance.professional_name else "",
                "email": instance.professional_email,
            },
            "service_id": instance.service_id,
            "start_time": instance.start_time.strftime("%H:%M"),
            "end_time": instance.end_time.strftime("%H:%M"),
        }


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description']
