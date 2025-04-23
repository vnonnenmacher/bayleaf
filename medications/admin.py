from django.contrib import admin
from .models import Medication, MedicationPrescription

admin.site.register(Medication)
admin.site.register(MedicationPrescription)