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
