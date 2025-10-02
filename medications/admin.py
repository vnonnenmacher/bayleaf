from django.contrib import admin
from .models import Medication, MedicationPrescription, MedicationItem, TakeMedicationEvent

admin.site.register(Medication)
admin.site.register(MedicationPrescription)
admin.site.register(MedicationItem)
admin.site.register(TakeMedicationEvent)
