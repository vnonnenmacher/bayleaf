from rest_framework import serializers
from .models import Service, Contact, Address, DosageUnit, Organization


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "code", "description"]


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for Address model."""
    class Meta:
        model = Address
        fields = ["id", "street", "city", "state", "zip_code", "country"]


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""
    class Meta:
        model = Contact
        fields = ["id", "phone_number", "email"]


class DosageUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DosageUnit
        fields = ("id", "code", "name")


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "code", "is_active")
