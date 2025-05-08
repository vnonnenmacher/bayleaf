import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from datetime import time, timedelta, datetime

from professionals.models import Role
from professionals.models import Professional, Shift, Specialization
from patients.models import Patient
from core.models import Service
from appointments.models import Appointment

fake = Faker()


class Command(BaseCommand):
    help = "Seed the database with test doctors, patients, shifts, and appointments."

    def add_arguments(self, parser):
        parser.add_argument('--doctors', type=int, default=10, help='Number of doctors to create')
        parser.add_argument('--patients', type=int, default=20, help='Number of patients to create')

    def handle(self, *args, **options):
        num_doctors = options['doctors']
        num_patients = options['patients']

        self.stdout.write(self.style.SUCCESS("Starting data seeding..."))

        # --- Step 1: Ensure at least one Role, Specialization, Service exists ---
        role, _ = Role.objects.get_or_create(name="General Practitioner", defaults={"description": "General medical doctor."})
        spec, _ = Specialization.objects.get_or_create(name="General Medicine", defaults={"description": "General practice."})
        service, _ = Service.objects.get_or_create(name="General Consultation")

        # --- Step 2: Create Doctors ---
        doctors = []
        for _ in range(num_doctors):
            email = fake.unique.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            doc = Professional.objects.create_user(
                email=email,
                password="password123",
                first_name=first_name,
                last_name=last_name
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
                Shift.objects.create(
                    professional=doc,
                    weekday=weekday,
                    service=service,
                    from_time=time(from_hour, 0),
                    to_time=time(to_hour, 0),
                    slot_duration=30
                )

        # --- Step 3: Create Patients ---
        patients = []
        for _ in range(num_patients):
            email = fake.unique.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            patient = Patient.objects.create_user(
                email=email,
                password="password123",
                first_name=first_name,
                last_name=last_name
            )
            patients.append(patient)
            self.stdout.write(f"Created patient {patient}")

        # --- Step 4: Create Appointments ---
        for patient in patients:
            num_appointments = random.randint(1, 20)
            for _ in range(num_appointments):
                doctor = random.choice(doctors)
                shift = random.choice(doctor.shifts.all())
                appointment_time = self._get_random_datetime_within_a_year()

                # Determine the status
                now = timezone.now()
                if appointment_time < now:
                    status = "COMPLETED"
                else:
                    status = random.choice(["REQUESTED", "CONFIRMED"])

                Appointment.objects.create(
                    professional=doctor,
                    patient=patient,
                    service=service,
                    shift=shift,
                    scheduled_to=appointment_time,
                    duration_minutes=shift.slot_duration,
                    description=f"Auto-generated appointment between {patient} and {doctor}",
                    created_by=patient,
                    status=status
                )
                self.stdout.write(
                    f"Booked {status} appointment for {patient} with {doctor} at {appointment_time.strftime('%Y-%m-%d %H:%M')}"
                )

    # --- Helper method ---
    def _get_random_datetime_within_a_year(self):
        """Generate a random datetime between -1 year and +1 year from now."""
        now = timezone.now()
        start = now - timedelta(days=365)
        end = now + timedelta(days=365)
        random_timestamp = random.uniform(start.timestamp(), end.timestamp())
        return datetime.fromtimestamp(random_timestamp, tz=timezone.get_current_timezone())
