from django.contrib import admin

from lab.models import SampleType, AllowedStateTransition, SampleState


# Register your models here.
@admin.register(SampleType)
class SampleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)


class AllowedStateTransitionInline(admin.TabularInline):
    model = AllowedStateTransition
    fk_name = 'from_state'  # Important: which side of the FK we are inlining
    extra = 1  # how many blank entries to show by default
    autocomplete_fields = ['to_state']  # optional, makes selecting to_state easier


@admin.register(SampleState)
class SampleStateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_initial_state', 'is_final_state', 'created_at']
    search_fields = ['name']
    inlines = [AllowedStateTransitionInline]


@admin.register(AllowedStateTransition)
class AllowedStateTransitionAdmin(admin.ModelAdmin):
    list_display = ['from_state', 'to_state']
    autocomplete_fields = ['from_state', 'to_state']
