import random
from decimal import Decimal
from datetime import time, timedelta, datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import get_current_timezone, make_aware
from django.db import transaction
from faker import Faker

from professionals.models import Role, Professional, Shift, Specialization, ServiceSlot
from patients.models import Patient
from core.models import Service, DosageUnit
from appointments.models import Appointment
from medications.models import MedicationItem, Medication

fake = Faker()


class Command(BaseCommand):
    help = "Seed the database with test doctors, patients, shifts, slots, appointments, and medications."

    def add_arguments(self, parser):
        parser.add_argument("--doctors", type=int, default=10, help="Number of doctors to create")
        parser.add_argument("--patients", type=int, default=20, help="Number of patients to create")
        parser.add_argument("--attach-medications", action="store_true",
                            help="If provided, attaches 1–5 random MedicationItems to each created patient")
        parser.add_argument("--slot-window-days", type=int, default=90,
                            help="Days window for slot generation (default 90).")
        parser.add_argument("--future-only", action="store_true",
                            help="Generate slots only from today forward (default includes past+future).")

    def handle(self, *args, **options):
        num_doctors = options["doctors"]
        num_patients = options["patients"]
        attach_meds = options.get("attach_medications") is True
        slot_window_days = int(options.get("slot_window_days") or 90)
        future_only = options.get("future_only", False)

        self.stdout.write(self.style.SUCCESS("Starting data seeding..."))

        # --- Ensure at least one Role, Specialization, Service ---
        role, _ = Role.objects.get_or_create(
            name="General Practitioner", defaults={"description": "General medical doctor."}
        )
        spec, _ = Specialization.objects.get_or_create(
            name="General Medicine", defaults={"description": "General practice."}
        )
        service, _ = Service.objects.get_or_create(
            name="General Consultation",
            defaults={"code": "GEN-CONSULT", "description": "General practice consult."},
        )

        # --- Doctors and Shifts ---
        doctors = []
        for _ in range(num_doctors):
            email = fake.unique.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            doc = Professional.objects.create_user(
                email=email, password="password123", first_name=first_name, last_name=last_name
            )
            doc.role = role
            doc.save()
            doc.specializations.add(spec)
            doc.services.add(service)
            doctors.append(doc)
            self.stdout.write(f"Created doctor {doc}")

            # Create 2 shifts per doctor
            weekdays = random.sample(range(0, 7), 2)
            for weekday in weekdays:
                from_hour = random.randint(8, 12)
                to_hour = from_hour + random.randint(1, 4)
                shift = Shift.objects.create(
                    professional=doc,
                    weekday=weekday,
                    service=service,
                    from_time=time(from_hour, 0),
                    to_time=time(to_hour, 0),
                    slot_duration=30,
                )
                self.stdout.write(f"  + Shift {shift}")

        # --- ServiceSlots ---
        self._generate_service_slots_for_all_shifts(slot_window_days, future_only)

        # --- Patients ---
        patients = []
        for _ in range(num_patients):
            email = fake.unique.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            patient = Patient.objects.create_user(
                email=email, password="password123", first_name=first_name, last_name=last_name
            )
            patients.append(patient)
            self.stdout.write(f"Created patient {patient}")

        # --- Medications ---
        if attach_meds:
            self._attach_random_medications(patients)

        # --- Appointments ---
        now = timezone.now()
        for patient in patients:
            num_appointments = random.randint(1, 10)
            for _ in range(num_appointments):
                doctor = random.choice(doctors)
                qs = ServiceSlot.objects.filter(shift__professional=doctor).select_related("shift")
                if not qs.exists():
                    continue
                slot = qs.order_by("?").first()

                appointment_time = slot.start_time
                status = "COMPLETED" if appointment_time < now else random.choice(["REQUESTED", "CONFIRMED"])
                duration_minutes = int((slot.end_time - slot.start_time).total_seconds() // 60)

                Appointment.objects.create(
                    professional=doctor,
                    patient=patient,
                    service=slot.shift.service,
                    service_slot=slot,
                    scheduled_to=appointment_time,
                    duration_minutes=duration_minutes,
                    description=f"Auto-generated appointment between {patient} and {doctor}",
                    created_by=patient,
                    status=status,
                )
                self.stdout.write(
                    f"Booked {status} appointment for {patient} with {doctor} at {appointment_time.strftime('%Y-%m-%d %H:%M')}"
                )

        self.stdout.write(self.style.SUCCESS("Seeding completed."))

    # ----------------- Helpers -----------------

    def _generate_service_slots_for_all_shifts(self, window_days: int, future_only: bool):
        tz = get_current_timezone()
        today = timezone.localdate()
        start_day = today if future_only else today - timedelta(days=window_days // 2)
        end_day = today + timedelta(days=window_days // 2)

        total_slots = 0
        to_create = []
        with transaction.atomic():
            for shift in Shift.objects.all().select_related("professional", "service"):
                weekday = shift.weekday
                days_offset = (weekday - start_day.weekday()) % 7
                first_day = start_day + timedelta(days=days_offset)
                d = first_day
                while d <= end_day:
                    start_dt = make_aware(datetime.combine(d, shift.from_time), tz)
                    end_dt = make_aware(datetime.combine(d, shift.to_time), tz)
                    cursor = start_dt
                    step = timedelta(minutes=shift.slot_duration)
                    while cursor + step <= end_dt:
                        to_create.append(ServiceSlot(shift=shift, start_time=cursor, end_time=cursor + step))
                        cursor += step
                    d += timedelta(days=7)
            ServiceSlot.objects.bulk_create(to_create, ignore_conflicts=True)
            total_slots = len(to_create)
        self.stdout.write(self.style.SUCCESS(f"Generated ServiceSlots: {total_slots}"))

    def _attach_random_medications(self, patients):
        meds = list(Medication.objects.all())
        units = list(DosageUnit.objects.all())
        if not meds or not units:
            self.stdout.write(self.style.WARNING("No Medications or DosageUnits in DB. Skipping medication seeding."))
            return

        for patient in patients:
            count = random.randint(1, 5)
            for _ in range(count):
                try:
                    med = random.choice(meds)
                    unit = random.choice(units)
                    MedicationItem.objects.create(
                        prescription=None,   # patient-entered, not doctor-prescribed
                        medication=med,
                        dosage_amount=Decimal(str(random.choice([5, 10, 20, 40, 250, 500, 1000]))),
                        dosage_unit=unit,
                        frequency_hours=random.choice([8, 12, 24]),   # interval in hours
                        instructions=fake.sentence(nb_words=10),
                        total_unit_amount=random.randint(10, 60),
                        patient=patient       # also comes from AbstractPrescriptionItem
                    )
                    self.stdout.write(f"  + Added medication for {patient} ({med})")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"  ! Skipped one medication for {patient} due to error: {e}"
                    ))
