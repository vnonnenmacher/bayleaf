# 🌿 Bayleaf - Open HealthTech API

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

### 1️⃣ **Clone the Repository**
```sh
git clone https://github.com/your-username/bayleaf.git
cd bayleaf
```

### 2️⃣ **Build the images
```sh
docker compose build
```

### 2️⃣ **Run the compose
```sh
docker compose up
```

Your API will be live at: **`http://127.0.0.1:8000/`**

---

## 🔗 API Endpoints & cURL Examples

### 🏥 **User Authentication**
#### ✅ Login (Obtain JWT Token)
```sh
curl -X POST http://127.0.0.1:8000/api/users/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "securepassword"}'
```
**Response:**
```json
{
    "access": "<your-access-token>",
    "refresh": "<your-refresh-token>"
}
```

### 👨‍⚕️ **Doctors**
#### ✅ Register a Doctor
```sh
curl -X POST http://127.0.0.1:8000/api/doctors/register/ \
     -H "Content-Type: application/json" \
     -d '{
           "did": "D123456",
           "email": "doctor@example.com",
           "password": "securepassword",
           "first_name": "Alice",
           "last_name": "Smith",
           "birth_date": "1985-08-15"
         }'
```
#### ✅ Retrieve Doctor Details
```sh
curl -X GET http://127.0.0.1:8000/api/doctors/retrieve/ \
     -H "Authorization: Bearer <your-access-token>"
```

### 🏥 **Patients**
#### ✅ Register a Patient
```sh
curl -X POST http://127.0.0.1:8000/api/patients/register/ \
     -H "Content-Type: application/json" \
     -d '{
           "pid": "P123456",
           "email": "patient@example.com",
           "password": "securepassword",
           "first_name": "John",
           "last_name": "Doe",
           "birth_date": "1990-05-20"
         }'
```
#### ✅ Retrieve Patient Details
```sh
curl -X GET http://127.0.0.1:8000/api/patients/retrieve/ \
     -H "Authorization: Bearer <your-access-token>"
```

### 🏥 **Appointments**
#### ✅ Check Available Slots
```sh
curl -X POST http://127.0.0.1:8000/api/appointments/available-slots/ \
     -H "Authorization: Bearer <your-access-token>" \
     -H "Content-Type: application/json" \
     -d '{
           "start_datetime": "2025-03-01T08:00:00",
           "end_datetime": "2025-03-01T18:00:00",
           "service": 3
         }'
```
#### ✅ Book an Appointment
```sh
curl -X POST http://127.0.0.1:8000/api/appointments/book/ \
     -H "Authorization: Bearer <your-access-token>" \
     -H "Content-Type: application/json" \
     -d '{
           "doctor": 2,
           "patient": 5,
           "service": 3,
           "date_time": "2025-03-01T09:00:00"
         }'
```

---

## 🤝 Contributing

We ❤️ contributions! To contribute:

1. **Fork** the repo & create a new branch
2. Make your changes & commit with a clear message
3. Submit a **Pull Request** (PR)

Check our [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## ⚖️ License
Bayleaf is open-source under the **GPL-2.0 License**. See [LICENSE](LICENSE) for details.

---

### 🚀 Let’s build the future of HealthTech together!

