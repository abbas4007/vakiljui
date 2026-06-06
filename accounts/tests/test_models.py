import pytest
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_creation():
    user = UserFactory()
    assert user.id is not None


def test_password_check():
    user = UserFactory(password="123")
    assert user.check_password("123")