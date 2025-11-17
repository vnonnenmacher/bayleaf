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
    help = "Seeds an Acute Flu CarePlanTemplate and creates a randomized instance with 1–3 random medications."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding Flu Care Plan Template..."))

        # ================================================================
        # TEMPLATE
        # ================================================================
        template, created = CarePlanTemplate.objects.get_or_create(
            name="Acute Flu – Symptom Management",
            version="1.0.0",
            defaults={
                "summary": "Short-term care plan for influenza symptom management, hydration, medication, and red flag monitoring.",
                "is_published": True,
                "applicability_json": {"target": "flu", "duration_days": 10},
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created template: {template}"))
        else:
            self.stdout.write(self.style.WARNING(f"→ Template already exists: {template} (updating components)"))

        # ================================================================
        # GOALS
        # ================================================================
        GoalTemplate.objects.update_or_create(
            template=template,
            title="Reduce fever within 72 hours",
            defaults={
                "description": "Symptom improvement target: restore normal temperature.",
                "target_metric_code": "body_temp_c",
                "target_value": {"max": 37.5},
                "timeframe_days": 3,
            },
        )

        GoalTemplate.objects.update_or_create(
            template=template,
            title="Improve overall flu symptoms by day 5",
            defaults={
                "description": "Fatigue, headache, chills, cough, and sore throat should improve by day 5.",
                "target_metric_code": "symptom_score",
                "target_value": {"max_score": 3},
                "timeframe_days": 5,
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Added GoalTemplates"))

        # ================================================================
        # ACTION TEMPLATES
        # ================================================================

        # Medication — antiviral/analgesic/antipyretic (actual item randomized per instance)
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Take your flu medication",
            defaults={
                "category": ActionTemplateCategory.MEDICATION,
                "instructions_richtext": "Take the prescribed flu medication daily.",
                "schedule_json": {"frequency": "DAILY", "at_time": "09:00"},
                "order_index": 0,
            },
        )

        # Daily temperature check
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Daily temperature check",
            defaults={
                "category": ActionTemplateCategory.MEASUREMENT,
                "instructions_richtext": "Measure body temperature each morning.",
                "schedule_json": {"frequency": "DAILY", "at_time": "08:00"},
                "order_index": 1,
            },
        )

        # Education: hydration + rest
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Hydration and rest guidance",
            defaults={
                "category": ActionTemplateCategory.EDUCATION,
                "instructions_richtext": "Drink plenty of fluids, rest, and avoid strenuous activity.",
                "schedule_json": {"on_start": True},
                "order_index": 2,
            },
        )

        # Red flags monitoring
        ActionTemplate.objects.update_or_create(
            template=template,
            title="Monitor for red flags",
            defaults={
                "category": ActionTemplateCategory.TASK,
                "instructions_richtext": """
                Seek urgent care if you experience difficulty breathing, chest pain, 
                confusion, persistent fever over 39°C, or dehydration symptoms.
                """,
                "schedule_json": {"frequency": "DAILY", "at_time": "12:00"},
                "order_index": 3,
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Added ActionTemplates"))

        # ================================================================
        # RANDOM INSTANCE CREATION
        # ================================================================
        patient = Patient.objects.all().order_by("?").first()
        if not patient:
            self.stdout.write(self.style.WARNING("⚠ No patients found; skipping instance creation."))
            return

        medications = list(MedicationItem.objects.all())
        if not medications:
            self.stdout.write(self.style.WARNING("⚠ No medications found; skipping medication details."))
            return

        # Random selection between 1 and 3 meds
        chosen_meds = random.sample(medications, random.randint(1, min(3, len(medications))))

        careplan = CarePlan.objects.create(
            patient=patient,
            template=template,
            status="ACTIVE",
            start_date=timezone.now().date(),
        )

        self.stdout.write(self.style.SUCCESS(
            f"✓ Created Flu CarePlan instance #{careplan.pk} for patient {patient.first_name} {patient.last_name}"
        ))

        # ================================================================
        # CREATE GOALS
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
        # CREATE ACTIONS
        # ================================================================
        for tmpl in template.activity_templates.all():
            action = CarePlanAction.objects.create(
                careplan=careplan,
                template=tmpl,
                category=tmpl.category,
                title=tmpl.title,
                status="PLANNED",
            )

            if tmpl.category == ActionTemplateCategory.MEDICATION:
                med_item = random.choice(chosen_meds)

                MedicationActionDetail.objects.create(
                    action=action,
                    medication_item=med_item,
                    dose="1 dose",
                    route="oral",
                    frequency="daily",
                    duration_days=7,
                )

                self.stdout.write(self.style.SUCCESS(
                    f"  → MedicationActionDetail: {med_item.medication.name} for '{action.title}'"
                ))

        self.stdout.write(self.style.SUCCESS("🎉 Flu Care Plan Template seeded successfully!"))
