import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from professionals.models import Professional


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(email="user@example.com", password="password")


@pytest.fixture
def professional(db):
    return Professional.objects.create(
        email="pro@example.com",
        first_name="Pro",
        last_name="User",
        password="password",
    )
