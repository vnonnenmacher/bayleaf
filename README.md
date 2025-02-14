🌿 Bayleaf - Open HealthTech API

Bayleaf is an open-source Django-based API designed to accelerate HealthTech MVP development. It provides a robust, extensible foundation for managing patients, authentication, and medical data with a modular and scalable approach.





🚀 Features

✅ Custom User Model with email-based authentication

✅ Patient Management with unique PID system

✅ Extensible Identifier System (e.g., National ID, Driver’s License)

✅ RESTful API powered by Django REST Framework

✅ Open-source & community-driven

🛠 Installation & Setup

1️⃣ Clone the Repository

git clone https://github.com/your-username/bayleaf.git
cd bayleaf

2️⃣ Create & Activate Virtual Environment

python -m venv env
source env/bin/activate  # macOS/Linux
env\Scripts\activate  # Windows

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Apply Migrations & Run Server

python manage.py migrate
python manage.py runserver

Your API will be live at: http://127.0.0.1:8000/

🔗 API Endpoints

Method

Endpoint

Description

POST

/api/patients/register/

Create a new patient

GET

/api/patients/{pid}/

Retrieve patient details

For full API documentation, see our Swagger/OpenAPI Docs (Coming Soon!).

🤝 Contributing

We ❤️ contributions! To contribute:

Fork the repo & create a new branch

Make your changes & commit with a clear message

Submit a Pull Request (PR)

Check our CONTRIBUTING.md for more details.

⚖️ License

Bayleaf is open-source under the MIT License. See LICENSE for details.

🚀 Let’s build the future of HealthTech together!