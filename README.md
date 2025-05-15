# 🌿 Bayleaf - Open HealthTech API

Bayleaf is a modular, scalable backend platform for healthcare applications, built with Django and Django REST Framework. It serves as the foundation for white-label apps that manage doctors, patients, appointments, medications, and more.

---

## 🚀 Features

- **User Management**
  - Professional-oriented user model with dynamic roles
  - Easily represent doctors, nurses, caregivers, attendants, or any other health professional
  - Identifier system with custom types (e.g., CRM, insurance ID)

- **Scheduling and Booking**
  - Synchronous and asynchronous appointment flows
  - Shift and availability management per doctor
  - Booking, cancellation, confirmation, and completion endpoints

- **Organizations and Services**
  - Many-to-many doctor–organization relationships
  - Service catalog with support for specializations and service types

- **Medications & Vaccines**
  - Segmented vaccine tracking (Upcoming / Taken)
  - Medication list and documentation features

- **Event System**
  - Centralized event model for appointments, medication events, and more
  - Status transitions and lifecycle management

- **Biological Sample Tracking (Planned)**
  - Blockchain-based internal audit trail for lab sample handling

---

## ⚙️ Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** Configurable in `settings.py` (default: MySQL)
- **Task Queue:** Celery + Redis
- **Caching:** Redis
- **Dev Tools:** Docker, Django Admin, Management Commands

---

## 🛡 Compliance

Bayleaf is designed with regulatory compliance in mind:

- **HIPAA (US)**
- **LGPD (Brazil)**

---

## 🧪 Local Development

```bash
# Clone the repo
$ git clone https://github.com/your-org/bayleaf-backend.git
$ cd bayleaf-backend

# Set up virtualenv
$ python -m venv env
$ source env/bin/activate

# Install dependencies
$ pip install -r requirements.txt

# Run migrations and start the server
$ python manage.py migrate
$ python manage.py runserver
```

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

## 📋 License

[GPL-2.0 license](./LICENSE)

---
