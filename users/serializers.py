from rest_framework import serializers
from users.models import Identifier, IdentifierType


class IdentifierSerializer(serializers.ModelSerializer):
    """Serializer for managing user identifiers."""

    type = serializers.CharField()  # ✅ Accepts a string instead of an ID

    class Meta:
        model = Identifier
        fields = ["type", "value"]

    def create(self, validated_data):
        """Ensures IdentifierType is created if it doesn’t exist."""
        type_name = validated_data.pop("type")  # Extract type as a string
        identifier_type, _ = IdentifierType.objects.get_or_create(name=type_name)  # ✅ Create if not exists
        validated_data["type"] = identifier_type  # Assign the newly created type
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Allows updating identifier using type name instead of id."""
        if "type" in validated_data:
            type_name = validated_data.pop("type")
            identifier_type, _ = IdentifierType.objects.get_or_create(name=type_name)
            instance.type = identifier_type  # ✅ Update type

        instance.value = validated_data.get("value", instance.value)
        instance.save()
        return instance
