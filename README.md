# 🌿 Bayleaf - Open HealthTech API

Bayleaf is a modular, scalable backend platform for healthcare applications, built with Django and Django REST Framework. It serves as the foundation for white-label apps that manage doctors, patients, appointments, medications, and more.

---

## ⚙️ Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** Configurable in `settings.py` (default: MySQL)
- **Task Queue:** Celery + Redis
- **Caching:** Redis
- **Dev Tools:** Docker, Django Admin, Management Commands

---

## Apps

Bayleaf is organized as Django apps with clear ownership boundaries:

- **appointments:** booked visits between professionals and patients; ties together services, slots, and scheduled event timing.
- **careplans:** care plan templates and patient-specific plans with goals and scheduled actions (medications, appointments, tasks).
- **core:** shared primitives like services, addresses, contacts, dosage units, and a lightweight timestamp mixin.
- **events:** base event lifecycle, status transitions, scheduling helpers, and audit history used across time-based features.
- **lab:** lab catalog (exams, versions, fields, tags), exam requests, and sample tracking with state transitions.
- **medications:** medication catalog, prescriptions and items, and scheduled "take medication" events.
- **patients:** patient records plus caregiver/relative relationships.
- **prescriptions:** abstract prescription and item models used by medications and other clinical modules.
- **professionals:** clinician profiles, roles, specializations, shifts, and service slots.
- **timeline:** API layer for assembling patient timelines from appointments and other events.
- **users:** custom auth user model, person profile fields, and identifiers.

---

## 🛡 Compliance

Bayleaf is designed with regulatory compliance in mind:

- **HIPAA (US)**
- **LGPD (Brazil)**

---

## 🧪 Local Development

Bayleaf runs with Docker Compose profiles.

```bash
# Start local stack (dev profile)
$ docker compose --profile dev up --force-recreate
```

## 🚀 Production

Create a production env file and run the prod profile:

```bash
# Copy and fill environment variables
$ cp .env.prod.example .env.prod

# Build and start production stack
$ docker compose --profile prod --env-file .env.prod up --build --force-recreate -d
```

### Production setup checklist

- Set `DJANGO_SECRET_KEY` and any database/redis credentials in `.env.prod`.
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Ensure volumes/paths in `docker-compose.yml` are correct for the host.

---

## ✅ Tests (pytest)

```bash
# Run only lab tests
$ pytest lab/tests
```

Pytest uses `bayleaf.settings.dev` by default (see `pytest.ini`). Override if needed:

```bash
$ DJANGO_SETTINGS_MODULE=bayleaf.settings.dev pytest lab/tests
```

### Writing tests (pytest)

Guidelines for adding new tests:

- Prefer fixtures over mocks to create real data (e.g., model instances) and keep tests readable.
- Use mocks only when asserting that a collaborator was called with specific parameters.
- Keep tests close to the app under `app_name/tests/` and follow the `test_*.py` pattern.
- Use `pytest.mark.django_db` for tests that touch the database.
- Keep tests focused on one behavior, and name them to describe intent.

---

## 📚 API Documentation

The API is versioned and RESTful.

- Swagger UI: `http://localhost:8000/api/docs/` (if enabled via drf-yasg)
- Django Admin Panel: `http://localhost:8000/admin/`
- Postman Workspace: [Bayleaf API on Postman](https://www.postman.com/sierralogics/workspace/bayleaf-api)
- Authentication: Token-based (JWT or Session depending on environment)

---

## 🥉 Frontend

Bayleaf pairs with [bayleaf-flutter](https://github.com/vnonnenmacher/bayleaf-flutter) — a Flutter-based **patient app**.

---

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

- Fork the Project

- Create your Feature Branch (git checkout -b feature/AmazingFeature)

- Commit your Changes (git commit -m 'Add some AmazingFeature')

- Push to the Branch (git push origin feature/AmazingFeature)

- Open a Pull Request

---

## License

This project is licensed under the GNU General Public License v2.0 (GPL-2.0).

---

## ⚠️ Requirements when redistributing:

You must keep the same license (GPL-2.0) for derivative works.

You must provide the full source code to end users.

You must include copyright and license notices.

---

## 💼 Commercial License

For companies or organizations that wish to:

- Integrate this software into proprietary solutions.

- Distribute modified versions without releasing the source code.

- Develop exclusive features under private contracts.

A commercial license is available upon request.

For inquiries or to acquire a commercial license, contact:

Email: vnonnenmacher@gmail.com
© 2025 Nonnenmacher Tecnologia Ltda
