import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_login(client):
    user = UserFactory()
    user.set_password("12345")
    user.save()

    response = client.post(reverse("accounts:login"), {
        "username": user.username,
        "password": "12345"
    })

    assert response.status_code in [200, 302]


def test_logout(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("accounts:logout"))
    assert response.status_code == 302