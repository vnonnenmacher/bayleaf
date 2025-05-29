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

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

- Fork the Project

- Create your Feature Branch (git checkout -b feature/AmazingFeature)

- Commit your Changes (git commit -m 'Add some AmazingFeature')

- Push to the Branch (git push origin feature/AmazingFeature)

- Open a Pull Request

License
This project is licensed under the GNU General Public License v2.0 (GPL-2.0).

## ✅ What you can do under the GPL-2.0:
Use, modify, and redistribute the source code freely.

Distribute modified versions, provided they are also under the GPL-2.0.

Access the complete source code of any distributed version.

## ⚠️ Requirements when redistributing:
You must keep the same license (GPL-2.0) for derivative works.

You must provide the full source code to end users.

You must include copyright and license notices.

## 💼 Commercial License
For companies or organizations that wish to:

Integrate this software into proprietary solutions.

Distribute modified versions without releasing the source code.

Develop exclusive features under private contracts.

A commercial license is available upon request.

For inquiries or to acquire a commercial license, contact:

Email: vnonnenmacher@gmail.com
© 2025 Nonnenmacher Tecnologia Ltda
