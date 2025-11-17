from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    CarePlanTemplate, GoalTemplate, ActionTemplate,
    CarePlan, CarePlanGoal, CarePlanAction,
    MedicationActionDetail, AppointmentActionDetail,
    CarePlanActivityEvent, CarePlanReview
)

# ============================================================
# TEMPLATE ADMIN
# ============================================================

class GoalTemplateInline(admin.StackedInline):
    model = GoalTemplate
    extra = 0
    show_change_link = True


class ActionTemplateInline(admin.StackedInline):
    model = ActionTemplate
    extra = 0
    show_change_link = True


@admin.register(CarePlanTemplate)
class CarePlanTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name", "version", "is_published",
        "created_by", "goal_count", "action_count",
        "created_at", "updated_at",
    ]
    list_filter = ["is_published", "created_by"]
    search_fields = ["name", "summary", "version"]
    inlines = [GoalTemplateInline, ActionTemplateInline]

    def goal_count(self, obj):
        return obj.goal_templates.count()

    def action_count(self, obj):
        return obj.activity_templates.count()


# ============================================================
# CAREPLAN ADMIN
# ============================================================

class CarePlanGoalInline(admin.TabularInline):
    model = CarePlanGoal
    extra = 0
    show_change_link = True


class CarePlanReviewInline(admin.StackedInline):
    model = CarePlanReview
    extra = 0
    readonly_fields = ["review_date"]
    show_change_link = True


class ActionInline(admin.TabularInline):
    model = CarePlanAction
    extra = 0
    readonly_fields = ["completed_at"]
    show_change_link = True


@admin.register(CarePlan)
class CarePlanAdmin(admin.ModelAdmin):
    list_display = [
        "id", "patient", "template", "colored_status",
        "owner", "start_date", "end_date",
        "created_at", "updated_at",
    ]
    list_filter = ["status", "owner", "template"]
    search_fields = ["patient__first_name", "patient__last_name"]
    inlines = [CarePlanGoalInline, ActionInline, CarePlanReviewInline]

    def colored_status(self, obj):
        colors = {
            "PLANNED": "gray",
            "ACTIVE": "green",
            "ON_HOLD": "orange",
            "COMPLETED": "blue",
            "CANCELLED": "red",
        }
        return format_html(
            f'<b><span style="color:{colors.get(obj.status, "black")}">{obj.status}</span></b>'
        )


# ============================================================
# ACTIONS + DETAILS ADMIN
# ============================================================

class MedicationDetailInline(admin.StackedInline):
    model = MedicationActionDetail
    extra = 0


class AppointmentDetailInline(admin.StackedInline):
    model = AppointmentActionDetail
    extra = 0


@admin.register(CarePlanAction)
class CarePlanActionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "category", "title", "careplan", "status",
        "assigned_to", "completed_at", "created_at",
    ]
    list_filter = ["category", "status", "assigned_to"]
    search_fields = ["title", "careplan__patient__first_name"]

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        if obj.category == "MEDICATION":
            return [MedicationDetailInline(self.model, self.admin_site)]
        if obj.category == "APPOINTMENT":
            return [AppointmentDetailInline(self.model, self.admin_site)]
        return []


# ============================================================
# EVENTS ADMIN (using ScheduledTimedEvent fields correctly)
# ============================================================

@admin.register(CarePlanActivityEvent)
class CarePlanActivityEventAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "action",
        "scheduled_to",
        "end_time",
        "created_at",
        "status",
    ]
    list_filter = ["scheduled_to", "action__category", "status"]
    search_fields = ["action__title"]

    def end_time(self, obj):
        return obj.get_end_time()

    end_time.short_description = "End"


# ============================================================
# REVIEWS ADMIN
# ============================================================

@admin.register(CarePlanReview)
class CarePlanReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "careplan", "reviewed_by", "review_date", "outcome"]
    list_filter = ["outcome", "reviewed_by"]
    search_fields = ["summary"]
    readonly_fields = ["review_date"]
