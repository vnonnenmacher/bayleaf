from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Address(models.Model):
    """
    Model to store address details.
    """
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state}, {self.country}"


class Contact(models.Model):
    """
    Model to store contact details.
    """
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.phone_number} ({self.email})" if self.email else self.phone_number


class DosageUnit(models.Model):
    """
    Represents a measurable unit for medication dosage (e.g., mg, mL, tablet).
    """
    code = models.CharField(max_length=20, unique=True)  # e.g. "mg"
    name = models.CharField(max_length=100)              # e.g. "Milligram"

    def __str__(self):
        return self.code
