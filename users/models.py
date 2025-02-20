from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.db import models
from core.models import Address, Contact  # Import from core app


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Empty since no more first_name/last_name

    def __str__(self):
        return self.email


from django.db import models
from datetime import date
from core.models import Address, Contact


class Person(models.Model):
    """
    Abstract model for users that represent real people (e.g., Patients, Doctors).
    """
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField(default=date(2000, 1, 1))  # ✅ Provide default value

    address1 = models.OneToOneField(
        Address, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name="%(class)s_primary_address1"
    )
    address2 = models.OneToOneField(
        Address, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name="%(class)s_secondary_address2"
    )
    primary_contact = models.OneToOneField(
        Contact, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name="%(class)s_primary_contact"
    )
    secondary_contact = models.OneToOneField(
        Contact, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name="%(class)s_secondary_contact"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class IdentifierType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Passport", "Driver’s License"

    def __str__(self):
        return self.name


class Identifier(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="identifiers")
    type = models.ForeignKey(IdentifierType, on_delete=models.CASCADE, related_name="identifiers")
    value = models.CharField(max_length=100, unique=True)  # e.g., passport number

    def __str__(self):
        return f"{self.type.name}: {self.value}"
