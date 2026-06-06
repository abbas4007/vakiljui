import pytest
from accounts.forms import SignupForm

pytestmark = pytest.mark.django_db


def test_signup_form_valid():
    form = SignupForm(data={
        "username": "test",
        "email": "test@test.com",
        "phone": "123",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
    })

    assert form.is_valid()