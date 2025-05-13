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

## 🗕 Upcoming

- Admin audit logs
- Role-based access control
- AI-assisted documentation tools
- Enhanced ML-based pricing engine

---

## 🤝 Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for setup and code style guides.

---

## 📋 License

[GPL-2.0 license](./LICENSE)

---


Bayleaf is an open-source **Django-based API** designed to accelerate HealthTech MVP development. It provides a robust, extensible foundation for managing **patients, doctors, appointments, and medical services** with a modular and scalable approach.

![Django](https://img.shields.io/badge/Django-5.0-green?style=flat-square)
![License](https://img.shields.io/badge/License-GPL--2.0-blue.svg)
![Contributions Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)

---

## 🚀 Features
- ✅ **Custom User Model** with email-based authentication
- ✅ **Doctor & Patient Management** with unique ID system
- ✅ **Extensible Identifier System** (e.g., National ID, Driver’s License)
- ✅ **Appointment Booking with Real-Time Slot Checking**
- ✅ **RESTful API powered by Django REST Framework**
- ✅ **Open-source & community-driven**

---

## 🛠 Installation & Setup

You will need docker engine installed on your server: https://docs.docker.com/engine/install/ubuntu/

### 1️⃣ **Clone the Repository**
```sh
git clone https://github.com/your-username/bayleaf.git
cd bayleaf
```

### 2️⃣ **Build the images**
```sh
docker compose build
```

### 2️⃣ **Run the compose**
```sh
docker compose up
```

Your API will be live at: **`http://127.0.0.1:8000/`**

---
