import pytest
from django.urls import reverse
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_lawyer_page(client):
    lawyer = UserFactory(is_lawyer=True, slug="lawyer-1")

    response = client.get(
        reverse("home:lawyer_detail", args=[lawyer.slug])
    )

    assert response.status_code == 200