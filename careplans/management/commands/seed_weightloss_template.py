from django.core.management.base import BaseCommand
from django.utils import timezone

from careplans.models import (
    CarePlanGoal,
    CarePlanTemplate,
    GoalTemplate,
    ActionTemplate,
    ActionTemplateCategory,
    CarePlan,
    CarePlanAction,
    ActionCategory,
    MedicationActionDetail,
)
from medications.models import MedicationItem
from patients.models import Patient


class Command(BaseCommand):
    help = "Seeds a Weight Loss CarePlanTemplate with goals, actions, and a sample instance."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding Weight Loss Care Plan Template..."))

        # ============================
        # TEMPLATE
        # ============================
        template, created = CarePlanTemplate.objects.get_or_create(
            name="Weight Loss – Basic Intro",
            version="1.0.0",
            defaults={
                "summary": "Introductory weight-loss plan with daily medication and weekly weigh-ins.",
                "is_published": True,
                "applicability_json": {"target": "weight_loss", "level": "beginner"},
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template}"))
        else:
            self.stdout.write(self.style.WARNING(f"→ Template already exists, updating: {template}"))

        # ============================
        # GOAL TEMPLATES
        # ============================
        GoalTemplate.objects.update_or_create(
            template=template,
            title="Lose 2–4 kg within 4 weeks",
            defaults={
                "description": "Targeted weight reduction in a 28-day period.",
                "target_metric_code": "weight_kg",
                "target_value": {"min_change": -4, "max_change": -2},
                "timeframe_days": 28,
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Added GoalTemplate"))

        # ============================
        # ACTION TEMPLATES
        # ============================

        # Daily medication reminder
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Take your daily weight-loss medication",
            defaults={
                "category": ActionTemplateCategory.MEDICATION,
                "instructions_richtext": "Take the prescribed medication once daily in the morning.",
                "schedule_json": {
                    "frequency": "DAILY",
                    "at_time": "08:00",
                },
                "order_index": 0,
            },
        )

        # Weekly weighing
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Weekly weight check",
            defaults={
                "category": ActionTemplateCategory.MEASUREMENT,
                "instructions_richtext": "Weigh yourself every Monday morning.",
                "schedule_json": {
                    "frequency": "WEEKLY",
                    "weekdays": ["MON"],
                    "at_time": "08:00",
                },
                "order_index": 1,
            },
        )

        # Education
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Read weight-loss introduction material",
            defaults={
                "category": ActionTemplateCategory.EDUCATION,
                "instructions_richtext": "Educational material to help understand weight-loss basics.",
                "schedule_json": {"on_start": True},
                "order_index": 2,
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Added ActionTemplates"))

        # ============================
        # OPTIONAL: CREATE SAMPLE INSTANCE
        # ============================

        patient = Patient.objects.all().order_by("?").first()
        medication = MedicationItem.objects.first()

        if not patient:
            self.stdout.write(self.style.WARNING("⚠ No patients found; skipping instance creation."))
            return

        if not medication:
            self.stdout.write(self.style.WARNING("⚠ No MedicationItem found; skipping medication detail."))
            return

        careplan = CarePlan.objects.create(
            patient=patient,
            template=template,
            status="ACTIVE",
            start_date=timezone.now().date(),
        )

        self.stdout.write(self.style.SUCCESS(f"✓ Created sample CarePlan instance #{careplan.pk}"))

        # ============================
        # CREATE GOALS FOR THE CAREPLAN
        # ============================

        for goal_tmpl in template.goal_templates.all():
            due = None
            if goal_tmpl.timeframe_days:
                due = timezone.now().date() + timezone.timedelta(days=goal_tmpl.timeframe_days)

            CarePlanGoal.objects.create(
                careplan=careplan,
                template=goal_tmpl,
                title=goal_tmpl.title,
                target_metric_code=goal_tmpl.target_metric_code,
                target_value_json=goal_tmpl.target_value,
                due_date=due,
                status="PLANNED",
            )

            self.stdout.write(self.style.SUCCESS(f"  → Added goal '{goal_tmpl.title}'"))


        # ============================
        # CREATE ACTIONS FOR THE CAREPLAN
        # ============================

        for tmpl in template.activity_templates.all():
            action = CarePlanAction.objects.create(
                careplan=careplan,
                template=tmpl,
                category=tmpl.category,
                title=tmpl.title,
                status="PLANNED",
            )

            # Create medication detail only for medication actions
            if tmpl.category == ActionTemplateCategory.MEDICATION:
                MedicationActionDetail.objects.create(
                    action=action,
                    medication_item=medication,
                    dose="1 dose",
                    route="oral",
                    frequency="daily",
                    duration_days=28,
                )

                self.stdout.write(self.style.SUCCESS(
                    f"  → Added MedicationActionDetail for '{action.title}'"
                ))


        self.stdout.write(self.style.SUCCESS("🎉 Weight-loss template seeded successfully!"))
