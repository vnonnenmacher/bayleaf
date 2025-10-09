# careplans/serializers.py
from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from professionals.models import Professional


from .models import (
    CarePlanTemplate, GoalTemplate, ActionTemplate,
    CarePlan, CarePlanGoal, CarePlanAction, CarePlanReview,
    MedicationActionDetail, AppointmentActionDetail, ActionCategory,
    CarePlanActivityEvent,
)


# ==========
# TEMPLATES
# ==========
class GoalTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalTemplate
        fields = [
            "id", "template", "title", "description",
            "target_metric_code", "target_value", "timeframe_days",
        ]


class ActionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionTemplate
        fields = [
            "id", "template", "title", "category", "instructions_richtext",
            "required_role", "schedule_json", "completion_criteria_json",
            "code", "order_index",
        ]


class CarePlanTemplateSerializer(serializers.ModelSerializer):
    goal_templates = GoalTemplateSerializer(many=True, read_only=True)
    activity_templates = ActionTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = CarePlanTemplate
        fields = [
            "id", "name", "summary", "version", "is_published",
            "applicability_json", "created_by", "created_at", "updated_at",
            "goal_templates", "activity_templates",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


# ====================
# ACTION DETAIL SERIALIZERS
# ====================
class MedicationActionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationActionDetail
        fields = ["medication_item", "dose", "route", "frequency", "duration_days"]


class AppointmentActionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentActionDetail
        fields = [
            "service", "specialization",
            "preferred_window_start", "preferred_window_end",
            "location_text", "is_virtual",
        ]


# ==============
# ACTIONS
# ==============
# careplans/serializers.py

class CarePlanActionSerializer(serializers.ModelSerializer):
    medication_detail = MedicationActionDetailSerializer(required=False)
    appointment_detail = AppointmentActionDetailSerializer(required=False)

    class Meta:
        model = CarePlanAction
        fields = [
            "id", "careplan", "template",
            "category", "title",
            "status", "cancel_reason", "completed_at",
            "custom_instructions_richtext",
            "assigned_to",
            "extras",
            "medication_detail", "appointment_detail",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    # ---------- validation ----------
    def _require_detail_for_category(self, category, med, appt):
        if category == ActionCategory.MEDICATION and not med:
            raise serializers.ValidationError("MEDICATION action requires medication_detail.")
        if category == ActionCategory.APPOINTMENT and not appt:
            raise serializers.ValidationError("APPOINTMENT action requires appointment_detail.")

    def validate(self, attrs):
        category = attrs.get("category") or getattr(self.instance, "category", None)

        if getattr(self, "partial", False) and self.instance:
            touching_med = "medication_detail" in attrs
            touching_appt = "appointment_detail" in attrs
            touching_cat = "category" in attrs

            if category == ActionCategory.MEDICATION and not (touching_med or touching_cat):
                return attrs
            if category == ActionCategory.APPOINTMENT and not (touching_appt or touching_cat):
                return attrs

        # Otherwise (create/PUT, or PATCH that *does* touch these), enforce as usual
        med = attrs.get("medication_detail")
        appt = attrs.get("appointment_detail")
        self._require_detail_for_category(category, med, appt)
        return attrs

    # ---------- create/update with nested detail ----------
    def _split_action_fields(self, validated):
        allowed = {
            "careplan", "template", "category", "title",
            "status", "cancel_reason", "completed_at",
            "custom_instructions_richtext", "assigned_to", "extras",
        }
        return {k: v for k, v in validated.items() if k in allowed}

    @transaction.atomic
    def create(self, validated_data):
        # ✅ pop nested, already-converted dicts (contain model instances)
        med_data = validated_data.pop("medication_detail", None)
        appt_data = validated_data.pop("appointment_detail", None)

        action = CarePlanAction.objects.create(**self._split_action_fields(validated_data))

        if med_data:
            MedicationActionDetail.objects.create(action=action, **med_data)
        if appt_data:
            AppointmentActionDetail.objects.create(action=action, **appt_data)
        return action

    @transaction.atomic
    def update(self, instance, validated_data):
        med_data = validated_data.pop("medication_detail", None)
        appt_data = validated_data.pop("appointment_detail", None)

        for field, value in self._split_action_fields(validated_data).items():
            setattr(instance, field, value)
        instance.save()

        if med_data is not None:
            if hasattr(instance, "medication_detail"):
                for k, v in med_data.items():
                    setattr(instance.medication_detail, k, v)
                instance.medication_detail.save()
            else:
                MedicationActionDetail.objects.create(action=instance, **med_data)

        if appt_data is not None:
            if hasattr(instance, "appointment_detail"):
                for k, v in appt_data.items():
                    setattr(instance.appointment_detail, k, v)
                instance.appointment_detail.save()
            else:
                AppointmentActionDetail.objects.create(action=instance, **appt_data)

        return instance


# ==========
# GOALS
# ==========
class CarePlanGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarePlanGoal
        fields = [
            "id", "careplan", "template",
            "title", "target_metric_code", "target_value_json",
            "due_date", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ==========
# REVIEWS
# ==========
class CarePlanReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarePlanReview
        fields = [
            "id", "careplan", "reviewed_by",
            "review_date", "summary", "outcome",
            "changes_json",
        ]

    read_only_fields = ["reviewed_by"]


# ==========
# CARE PLANS
# ==========

class CarePlanGoalInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarePlanGoal
        fields = [
            "template",
            "title",
            "target_metric_code",
            "target_value_json",
            "due_date",
            "status",
        ]


class CarePlanActionInlineSerializer(serializers.ModelSerializer):
    medication_detail = MedicationActionDetailSerializer(required=False)
    appointment_detail = AppointmentActionDetailSerializer(required=False)

    class Meta:
        model = CarePlanAction
        # No `careplan` here on purpose; we’ll attach it in the parent create()
        fields = [
            "template",
            "category",
            "title",
            "status",
            "cancel_reason",
            "completed_at",
            "custom_instructions_richtext",
            "assigned_to",
            "extras",
            "medication_detail",
            "appointment_detail",
        ]

    def validate(self, attrs):
        from .models import ActionCategory
        cat = attrs.get("category")
        # ✅ use attrs, not self.initial_data (which doesn't exist here)
        med = attrs.get("medication_detail")
        appt = attrs.get("appointment_detail")

        if cat == ActionCategory.MEDICATION and not med:
            raise serializers.ValidationError("MEDICATION action requires medication_detail.")
        if cat == ActionCategory.APPOINTMENT and not appt:
            raise serializers.ValidationError("APPOINTMENT action requires appointment_detail.")
        return attrs


class CarePlanSerializer(serializers.ModelSerializer):
    """
    Write-friendly plan serializer (minimal nesting).
    Professionals/agents can create a plan and optionally pass
    initial goals/actions (if you want that, use CarePlanUpsertSerializer below).
    """
    class Meta:
        model = CarePlan
        fields = [
            "id", "patient", "template", "status",
            "start_date", "end_date",
            "owner", "reason_codes", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CarePlanActionReadSerializer(CarePlanActionSerializer):
    """Read-only variant that always expands details."""
    medication_detail = MedicationActionDetailSerializer(read_only=True)
    appointment_detail = AppointmentActionDetailSerializer(read_only=True)


class CarePlanDetailSerializer(serializers.ModelSerializer):
    """
    Patient-friendly read serializer that returns the whole tree.
    Useful for: “list my plans with goals, actions, reviews”.
    """
    goals = CarePlanGoalSerializer(many=True, read_only=True)
    actions = CarePlanActionReadSerializer(many=True, read_only=True)
    reviews = CarePlanReviewSerializer(many=True, read_only=True)

    class Meta:
        model = CarePlan
        fields = [
            "id", "patient", "template", "status",
            "start_date", "end_date",
            "owner", "reason_codes", "notes",
            "goals", "actions", "reviews",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class CarePlanUpsertSerializer(CarePlanSerializer):
    """
    Optional: professionals/agents can create/update a plan *with* nested goals/actions.
    If you prefer to manage actions/goals via their own endpoints, you can skip this.
    """
    goals = CarePlanGoalInlineSerializer(many=True, required=False)
    actions = CarePlanActionInlineSerializer(many=True, required=False)

    class Meta(CarePlanSerializer.Meta):
        fields = CarePlanSerializer.Meta.fields + ["goals", "actions"]

    @transaction.atomic
    def create(self, validated_data):
        # pull nested payloads out first
        goals_data = validated_data.pop("goals", [])
        actions_data = validated_data.pop("actions", [])

        # -------- default owner = requesting Professional (if not provided) --------
        request = self.context.get("request")
        if not validated_data.get("owner") and request and request.user and request.user.is_authenticated:
            pro = Professional.objects.filter(user_ptr_id=request.user.id).first()
            if pro:
                validated_data["owner"] = pro

        # create plan
        plan = CarePlan.objects.create(**validated_data)

        # create goals (attach plan automatically)
        for g in goals_data:
            CarePlanGoal.objects.create(careplan=plan, **g)

        # create actions + per-category details
        for a in actions_data:
            med = a.pop("medication_detail", None)
            appt = a.pop("appointment_detail", None)

            action = CarePlanAction.objects.create(careplan=plan, **a)

            if med:
                MedicationActionDetail.objects.create(action=action, **med)
            if appt:
                AppointmentActionDetail.objects.create(action=action, **appt)

        return plan

    @transaction.atomic
    def update(self, instance, validated_data):
        # Only base plan fields here; modify goals/actions via their own endpoints
        return super().update(instance, validated_data)


# ============================
# SCHEDULED EVENTS (per action)
# ============================
class CarePlanActivityEventSerializer(serializers.ModelSerializer):
    """
    Serializer for the concrete scheduled occurrences tied to a CarePlanAction.
    This model inherits from events.ScheduledTimedEvent -> BaseEvent.

    - To change status, update with {"status": "..."}; we call BaseEvent.update_status()
      so VALID_TRANSITIONS are enforced and audit history is created.
    """
    class Meta:
        model = CarePlanActivityEvent
        # scheduled_to/duration_minutes come from ScheduledTimedEvent (abstract)
        fields = [
            "id", "action",
            "scheduled_to", "duration_minutes",
            "event_type", "description",
            "status", "created_at", "created_by",
            "rescheduled_to",
        ]
        read_only_fields = ["id", "event_type", "created_at", "created_by", "rescheduled_to"]

    def create(self, validated_data):
        # ensure we stamp who created the event
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authenticated user required to create an event.")
        return CarePlanActivityEvent.objects.create(created_by=user, **validated_data)

    def update(self, instance: CarePlanActivityEvent, validated_data):
        new_status = validated_data.get("status", None)
        if new_status and new_status != instance.status:
            instance.update_status(
                new_status,
                changed_by=self.context.get("request").user if self.context.get("request") else None
            )
            validated_data.pop("status", None)
        for field in ["description", "scheduled_to", "duration_minutes"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance
