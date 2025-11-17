import random
from django.core.management.base import BaseCommand
from django.utils import timezone

from careplans.models import (
    CarePlanTemplate,
    GoalTemplate,
    ActionTemplate,
    ActionTemplateCategory,
    CarePlan,
    CarePlanGoal,
    CarePlanAction,
    ActionCategory,
    MedicationActionDetail,
)
from medications.models import MedicationItem
from patients.models import Patient


class Command(BaseCommand):
    help = "Seeds a Cholesterol Reduction CarePlanTemplate and creates a randomized CarePlan instance with 1–3 random medications."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding Cholesterol Reduction Care Plan Template..."))

        # ================================================================
        # TEMPLATE
        # ================================================================
        template, created = CarePlanTemplate.objects.get_or_create(
            name="Cholesterol Reduction – Basic Control",
            version="1.0.0",
            defaults={
                "summary": "Care plan focused on lowering LDL cholesterol and stabilizing triglycerides.",
                "is_published": True,
                "applicability_json": {"target": "cholesterol", "level": "basic"},
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template}"))
        else:
            self.stdout.write(self.style.WARNING(f"→ Template already exists: {template}, updating components"))

        # ================================================================
        # GOAL TEMPLATES
        # ================================================================
        GoalTemplate.objects.update_or_create(
            template=template,
            title="Reduce LDL cholesterol by 10–20% in 8 weeks",
            defaults={
                "description": "LDL cholesterol reduction goal.",
                "target_metric_code": "ldl_mg_dl",
                "target_value": {"reduction_percent_min": 10, "reduction_percent_max": 20},
                "timeframe_days": 56,
            },
        )

        GoalTemplate.objects.update_or_create(
            template=template,
            title="Stabilize triglycerides",
            defaults={
                "description": "Keep triglycerides in a healthy range.",
                "target_metric_code": "triglycerides_mg_dl",
                "target_value": {"max": 150},
                "timeframe_days": 56,
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Added GoalTemplates"))

        # ================================================================
        # ACTION TEMPLATES
        # ================================================================

        # Medication daily (the actual medication will be randomized per instance)
        med_action_tmpl, _ = ActionTemplate.objects.update_or_create(
            template=template,
            title="Take your daily cholesterol medication",
            defaults={
                "category": ActionTemplateCategory.MEDICATION,
                "instructions_richtext": "Daily medication to help reduce cholesterol levels.",
                "schedule_json": {"frequency": "DAILY", "at_time": "08:00"},
                "order_index": 0,
            },
        )

        # Weekly lipid panel check
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Weekly fasting lipid measurement",
            defaults={
                "category": ActionTemplateCategory.MEASUREMENT,
                "instructions_richtext": "Measure fasting lipids every Monday morning.",
                "schedule_json": {"frequency": "WEEKLY", "weekdays": ["MON"], "at_time": "07:00"},
                "order_index": 1,
            },
        )

        # Education
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Read cholesterol-lowering lifestyle guidelines",
            defaults={
                "category": ActionTemplateCategory.EDUCATION,
                "instructions_richtext": "Educational material for diet, exercise, and lifestyle.",
                "schedule_json": {"on_start": True},
                "order_index": 2,
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Added ActionTemplates"))

        # ================================================================
        # RANDOMIZED INSTANCE CREATION
        # ================================================================

        patient = Patient.objects.all().order_by("?").first()
        if not patient:
            self.stdout.write(self.style.WARNING("⚠ No patients found; skipping instance creation."))
            return

        medications = list(MedicationItem.objects.all())
        if not medications:
            self.stdout.write(self.style.WARNING("⚠ No medications available; skipping medication details."))
            return

        # Choose between 1 and 3 medications
        chosen_meds = random.sample(medications, random.randint(1, min(3, len(medications))))

        careplan = CarePlan.objects.create(
            patient=patient,
            template=template,
            status="ACTIVE",
            start_date=timezone.now().date(),
        )

        self.stdout.write(self.style.SUCCESS(
            f"✓ Created Cholesterol CarePlan instance #{careplan.pk} for {patient.first_name} {patient.last_name}"
        ))

        # ================================================================
        # CREATE GOALS FOR THE INSTANCE
        # ================================================================
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

        # ================================================================
        # CREATE ACTIONS FOR THE INSTANCE
        # ================================================================
        for tmpl in template.activity_templates.all():
            action = CarePlanAction.objects.create(
                careplan=careplan,
                template=tmpl,
                category=tmpl.category,
                title=tmpl.title,
                status="PLANNED",
            )

            # Handle medication actions separately
            if tmpl.category == ActionTemplateCategory.MEDICATION:
                # Choose one of the random medications for THIS action
                med_item = random.choice(chosen_meds)

                MedicationActionDetail.objects.create(
                    action=action,
                    medication_item=med_item,
                    dose="1 dose",
                    route="oral",
                    frequency="daily",
                    duration_days=56,
                )

                self.stdout.write(self.style.SUCCESS(
                    f"  → MedicationActionDetail: {med_item.medication.name} for '{action.title}'"
                ))

        self.stdout.write(self.style.SUCCESS("🎉 Cholesterol template seeded successfully!"))
