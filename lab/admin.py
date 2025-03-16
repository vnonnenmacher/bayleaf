from django.contrib import admin

from lab.models import SampleType


# Register your models here.
@admin.register(SampleType)
class SampleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
